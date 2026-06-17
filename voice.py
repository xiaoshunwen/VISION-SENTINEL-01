import io
import time
import asyncio
from datetime import datetime
import pygame
import edge_tts
from openai import OpenAI
import config


class VoiceEngine:
    def __init__(self):
        self.client = OpenAI(api_key=config.QWEN_API_KEY, base_url=config.QWEN_BASE_URL)
        self.is_speaking = False  # 状态锁：防止哨兵说话时自己触发自己
        pygame.mixer.init()

    def get_ai_text(self, identity, custom_command=None):
        """请求通义千问获取不同语境下的文案"""
        hour = datetime.now().hour
        if 0 <= hour < 5:
            time_context = "凌晨深夜"
        elif 5 <= hour < 11:
            time_context = "上午时分"
        elif 11 <= hour < 14:
            time_context = "中午饭点"
        elif 14 <= hour < 18:
            time_context = "下午时分"
        else:
            time_context = "晚上夜间"

        try:
            if custom_command:
                p = f"你是一个傲娇可爱的AI少女。主人说：'{custom_command}'。请简短傲娇回应，不加标点，20字内。"
            elif identity != 'Stranger':
                p = f"你是一个傲娇可爱的少女。现在是{time_context}，成员 {identity} 回来了，请结合当前时间段对他进行简短的傲娇欢迎，绝对不加标点，15字内。"
            else:
                p = f"你是一个严厉的守卫。在这危险的{time_context}发现形迹可疑的陌生人，严厉骂他驱逐他，20字内。"

            completion = self.client.chat.completions.create(
                model="qwen-turbo",
                messages=[{'role': 'user', 'content': p}]
            )
            return completion.choices[0].message.content.strip()
        except:
            return "注意安全！"

    def play_voice_sync(self, text):
        """通过 Edge-TTS 生成并播放音频，带忙碌等待锁"""
        self.is_speaking = True
        try:
            async def _gen():
                communicate = edge_tts.Communicate(text, config.VOICE_NAME)
                audio_data = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data += chunk["data"]
                return audio_data

            audio_stream = io.BytesIO(asyncio.run(_gen()))
            pygame.mixer.music.load(audio_stream, "mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            print(f"[播放异常]: {e}")
        self.is_speaking = False