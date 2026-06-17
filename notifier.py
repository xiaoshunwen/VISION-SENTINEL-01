import json
import requests
import threading
from datetime import datetime
import config


def upload_to_image_bed(file_path):
    """上传抓拍图片到 ImgBB 图床"""
    if not config.IMGBB_API_KEY or config.IMGBB_API_KEY == "你的_IMGBB_API_KEY":
        print("[图床提示] 🛑 未配置或配置了错误的 ImgBB API Key！")
        return None
    try:
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": config.IMGBB_API_KEY}
        with open(file_path, "rb") as f:
            files = {"image": f}
            response = requests.post(url, data=payload, files=files, timeout=10)
        if response.status_code == 200:
            return response.json()["data"]["url"]
        else:
            print(f"[图床失败] 状态码: {response.status_code} | 原因: {response.text}")
    except Exception as e:
        print(f"[图床异常] 上传超时或网络异常: {e}")
    return None


def send_remote_alert(identity, msg, img_url=None):
    """异步发送钉钉警报消息"""

    def _task():
        try:
            headers = {'Content-Type': 'application/json'}
            now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if img_url:
                # Markdown 卡片模式
                data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": "🚨 哨兵系统指派提醒",
                        "text": f"### 🚨 发现陌生人入侵 (哨兵系统)\n"
                                f"**时间**：{now_time}\n\n"
                                f"**状态**：检测到 {identity}\n\n"
                                f"**详情**：{msg}\n\n"
                                f"![现场抓拍]({img_url})"
                    }
                }
            else:
                # 纯文本模式
                if "每周" in identity or "周报" in msg:
                    content_text = f"【哨兵系统周报】\n{msg}"
                else:
                    content_text = f"【哨兵系统警报】\n🚨 发现陌生人入侵\n时间：{now_time}\n状态：检测到 {identity}\n详情：{msg}"

                data = {
                    "msgtype": "text",
                    "text": {"content": content_text}
                }

            response = requests.post(config.DING_URL, data=json.dumps(data), headers=headers, timeout=5)
            print(f"[钉钉接口响应] 状态码: {response.status_code} | 返回结果: {response.text}")
        except Exception as e:
            print(f"推送发生网络级异常: {e}")

    threading.Thread(target=_task, daemon=True).start()