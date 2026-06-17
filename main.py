import os
import cv2
import time
import numpy as np
import threading
from datetime import datetime
import speech_recognition as sr

import config
import notifier
import logger
from face_rec import FaceEngine
from voice import VoiceEngine


class TalkingSentinel:
    def __init__(self):
        # 1. 初始化文件存储结构
        logger.init_folders_and_logs()

        # 2. 实例化各个解耦的引擎
        self.face_engine = FaceEngine()
        self.voice_engine = VoiceEngine()

        # 3. 运行控制逻辑变量
        self.last_person = None
        self.absence_frames = 0
        self.stranger_loop_active = False
        self.last_trigger_times = {}
        self.latest_frame = None  # 给异步报警线程共享最新画面

        # 4. 异步拉起语音唤醒线程
        threading.Thread(target=self._voice_listener_worker, daemon=True).start()
        print("--- Sentinel 已就绪 ---")

    def save_evidence_with_watermark(self, current_id, frame):
        """带水印的本地存证任务"""

        def _task(cid, img_copy):
            day_str = datetime.now().strftime("%Y-%m-%d")
            path = os.path.join(config.RECORD_DIR, day_str)
            if not os.path.exists(path): os.makedirs(path)
            time_str = datetime.now().strftime("%H:%M:%S")
            filename = f"{datetime.now().strftime('%H-%M-%S')}_{cid}.jpg"
            watermark_text = f"Time: {day_str} {time_str} | ID: {cid}"
            color = (0, 255, 0) if cid != "Stranger" else (0, 0, 255)
            cv2.putText(img_copy, watermark_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.imwrite(os.path.join(path, filename), img_copy)

        threading.Thread(target=_task, args=(current_id, frame.copy()), daemon=True).start()

    def stranger_warning_task(self):
        """陌生人循环警告与连续推送异步逻辑"""
        self.stranger_loop_active = True
        while self.last_person == "Stranger":
            msg = self.voice_engine.get_ai_text('Stranger')
            img_url = None
            if self.latest_frame is not None:
                try:
                    day_str = datetime.now().strftime("%Y-%m-%d")
                    path = os.path.join(config.RECORD_DIR, day_str)
                    if not os.path.exists(path): os.makedirs(path)
                    time_str = datetime.now().strftime("%H:%M:%S")
                    img_path = os.path.join(path, f"{datetime.now().strftime('%H-%M-%S')}_Stranger_Alarm.jpg")

                    img_copy = self.latest_frame.copy()
                    watermark_text = f"Time: {day_str} {time_str} | ID: Stranger"
                    cv2.putText(img_copy, watermark_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    cv2.imwrite(img_path, img_copy)
                    img_url = notifier.upload_to_image_bed(img_path)
                except Exception as e:
                    print(f"后台警报抓拍失败: {e}")

            notifier.send_remote_alert("未授权入侵", msg, img_url)
            self.voice_engine.play_voice_sync(msg)
            for _ in range(50):
                if self.last_person != "Stranger": break
                time.sleep(0.1)
        self.stranger_loop_active = False

    def _handle_master_command(self, command_text):
        """解析并执行主人的语音指令"""
        print(f"[语音指令解析] -> {command_text}")

        if any(k in command_text for k in ["有人来过", "谁来过", "今天情况", "几点"]):
            visitors = logger.get_today_visitors()
            if not visitors:
                self.voice_engine.play_voice_sync("报告主人，今天没有检测到任何人来过")
            else:
                summary_str = ", ".join([f"{v['name']}在{v['time']}" for v in visitors])
                p = f"你是一个贴心的AI哨兵。主人问你今天有谁来过。请根据这些记录写一句话汇报（100字内，不加标点）：{summary_str}"
                try:
                    comp = self.voice_engine.client.chat.completions.create(
                        model="qwen-turbo", messages=[{'role': 'user', 'content': p}]
                    )
                    reply = comp.choices[0].message.content.strip()
                except:
                    reply = f"今天一共检测到{len(visitors)}次到访"
                self.voice_engine.play_voice_sync(reply)

        elif any(k in command_text for k in ["一周", "整理", "报告", "文件"]):
            self.voice_engine.play_voice_sync("收到，正在为您汇总近一周数据，请稍候")
            file_path, count = logger.generate_weekly_report()
            try:
                if count == 0:
                    notifier.send_remote_alert("每周安全简报", "本周无任何识别记录。")
                    self.voice_engine.play_voice_sync("这周非常安静，没有任何记录")
                    return

                with open(file_path, 'r', encoding='utf-8') as f:
                    full_content = f.read()

                report_text = full_content[:1500] + "\n\n(注：内容过长已截断)" if len(
                    full_content) > 1500 else full_content
                notifier.send_remote_alert("每周安全汇总", report_text)
                self.voice_engine.play_voice_sync(f"报告已整理完毕，共{count}次记录，已推送到您的钉钉")
            except Exception as e:
                print(f"发送周报失败: {e}")
                self.voice_engine.play_voice_sync("抱歉主人，发送报告时出了一点小差错")
        else:
            reply = self.voice_engine.get_ai_text(None, custom_command=command_text)
            self.voice_engine.play_voice_sync(reply)

    def _voice_listener_worker(self):
        """后台麦克风监听工作线程"""
        r = sr.Recognizer()
        mic = sr.Microphone()
        while True:
            # 只有当已知的主人在场，且哨兵没有在说话时，才开始监听
            is_master_present = self.last_person and (self.last_person in self.face_engine.known_faces)
            if is_master_present and not self.voice_engine.is_speaking:
                with mic as source:
                    r.adjust_for_ambient_noise(source, duration=0.4)
                    try:
                        audio = r.listen(source, timeout=3, phrase_time_limit=3)
                        text = r.recognize_google(audio, language='zh-CN')

                        if "哨兵" in text:
                            print(f"[唤醒成功] 检测到主人呼唤")
                            self.voice_engine.play_voice_sync("您好主人请问有什么吩咐")
                            r.adjust_for_ambient_noise(source, duration=0.2)
                            cmd_audio = r.listen(source, timeout=5, phrase_time_limit=6)
                            cmd_text = r.recognize_google(cmd_audio, language='zh-CN')
                            if cmd_text.strip():
                                self._handle_master_command(cmd_text)
                    except (sr.WaitTimeoutError, sr.UnknownValueError):
                        pass
                    except Exception as e:
                        print(f"语音引擎异常: {e}")
            time.sleep(0.5)

    def run(self):
        """核心视频捕获与目标追踪状态机循环"""
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            success, frame = cap.read()
            if not success: break
            frame = cv2.flip(frame, 1)
            self.latest_frame = frame.copy()

            # 利用 780M 核显进行快速推理
            faces = self.face_engine.detect_faces(frame)
            valid_faces = [f for f in faces if f.det_score > 0.6]

            if not valid_faces:
                self.absence_frames += 1
                if self.absence_frames >= config.RESET_THRESHOLD:
                    self.last_person = None
            else:
                self.absence_frames = 0
                current_frame_masters = []
                has_stranger = False
                max_score_in_frame = 0.0

                for face in valid_faces:
                    best_score = 0
                    match_name = "Unknown"
                    for name, embedding in self.face_engine.known_faces.items():
                        score = np.dot(embedding, face.normed_embedding)
                        if score > best_score:
                            best_score, match_name = score, name

                    if best_score > max_score_in_frame:
                        max_score_in_frame = best_score

                    if best_score > 0.48:
                        display_name, box_color = match_name, (0, 255, 0)
                        current_frame_masters.append(match_name)
                    elif best_score < 0.28:
                        display_name, box_color = "Stranger", (0, 0, 255)
                        has_stranger = True
                    else:
                        display_name, box_color = "Scanning...", (0, 255, 255)

                    box = face.bbox.astype(int)
                    cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), box_color, 2)
                    cv2.putText(frame, f"{display_name} {best_score:.2f}", (box[0], box[1] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

                target_id = current_frame_masters[0] if current_frame_masters else (
                    "Stranger" if has_stranger else None)

                if target_id and target_id != self.last_person:
                    now_time = time.time()
                    last_trigger = self.last_trigger_times.get(target_id, 0)

                    if now_time - last_trigger > config.COOLDOWN_PERIOD:
                        self.last_person = target_id
                        self.last_trigger_times[target_id] = now_time

                        self.save_evidence_with_watermark(self.last_person, frame)
                        msg = self.voice_engine.get_ai_text(self.last_person)
                        logger.log_to_csv(self.last_person, max_score_in_frame, msg)

                        if self.last_person == "Stranger":
                            if not self.stranger_loop_active:
                                threading.Thread(target=self.stranger_warning_task, daemon=True).start()
                        else:
                            threading.Thread(target=lambda: self.voice_engine.play_voice_sync(msg), daemon=True).start()
                    else:
                        self.last_person = target_id

            cv2.imshow('Sentinel-Sync-Precision', frame)
            if cv2.waitKey(1) & 0xFF == 27: break
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    sentinel = TalkingSentinel()
    sentinel.run()