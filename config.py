import os

# --- 路径配置 ---
# 已知人脸文件夹和报警抓拍文件夹
FACES_DIR = "faces"
RECORD_DIR = "records"
LOG_FILE = "sentinel_report.csv"

# --- 核心算法参数 ---
RESET_THRESHOLD = 12       # 目标消失多少帧后重置状态
COOLDOWN_PERIOD = 30       # 同一人身份触发的冷却时间 (秒)
FACE_DET_SIZE = (640, 640)  # 人脸检测输入分辨率

# --- 语音配置 ---
VOICE_NAME = "zh-CN-XiaoxiaoNeural"

# --- 硬件加速配置 (针对 AMD Radeon 780M 优化) ---
EP_PROVIDERS = ['DmlExecutionProvider', 'CPUExecutionProvider']

# --- 敏感 API Keys ---
# 💡 提示：如果上传到公开平台，记得隐藏这部分内容
IMGBB_API_KEY = "YOUR_API_KEY"
DING_URL = "YOUR_DING_URL"
QWEN_API_KEY = "YOUR_QWEN_API_KEY"
QWEN_BASE_URL = "YOUR_QWEN_BASE_URL"