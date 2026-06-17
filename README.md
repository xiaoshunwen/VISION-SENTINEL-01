# VISION-SENTINEL-01
This involves equipping traditional cameras with AI agents, enabling real-time monitoring while endowing them with intelligence and vitality
# 🛡️ Vision-Sentinel-Agent (视觉哨兵自主追踪智能体)

一个基于边缘计算硬件、大语言模型（LLM）与闭环控制算法的**软硬件一体化实体视觉智能体**。系统不仅具备高精度的面部识别与多重人格语音交互能力，还拥有物理实体的“追踪之眼”——能根据目标（特别是未知入侵者）的位置动态，自主旋转双轴云台进行物理锁定与连续追踪。

---

## 🌟 核心特性 (Features)

- **⚡ 硬件加速推理**：深度适配 AMD Radeon 780M 核显（基于微软 DirectML 架构），实现本地 40~60 FPS 的低延迟高帧率边缘视觉计算。
- **🎯 物理闭环追踪**：基于经典的 **PID 控制算法**，实时计算目标面部与画面中心的像素偏差，通过串口驱动二维度舵机云台，实现平滑、精准的物理追踪锁定。
- **🧠 大模型动态交互**：接入通义千问大模型（Qwen API），结合当前时间、识别身份及用户自定义语音指令，动态生成傲娇少女或严厉守卫双重人格的语音文案。
- **🗣️ 全双工语音唤醒**：集成无线麦克风与 SpeechRecognition 模块，支持通过唤醒词“哨兵哨兵”触发多轮命令交互，实现人机无缝对话。
- **🚨 异步多级立体警报**：发现未知入侵者时，无感触发本地带水印存证、图床秒级上传、钉钉机器人富文本（Markdown）卡片现场画面推送。
- **📊 数据安全与本地周报**：本地 CSV 自动审计到访日志，支持通过语音指令让 AI 智能体自动汇总分析并生成“近一周安全事件文本简报”。

---

## 🛠️ 系统架构与硬件拓扑 (Architecture)

系统采用**“上位机推理决策 + 下位机动作执行”**的经典 AIoT 架构：

1. **上位机 (PC端)**：利用 AMD 强劲核显运行 `InsightFace` 模型流，进行人脸检测与特征比对。同时负责语音唤醒、大模型逻辑处理及网络告警。
2. **下位机 (单片机端)**：`ESP32` 或 `Arduino Uno` 接收上位机发来的位置偏差指令，转换为 PWM 信号驱动舵机。

```text
[ 摄像头 ] ---> (上位机: PC / Radeon 780M 加速) ---> [ PID 算法计算偏差 ]
                                                               |
                                                          (USB 串口通信)
                                                               |
[ 舵机云台 ] <--- (PWM 信号驱动) <--- (下位机: Arduino / ESP32) <-------+
```

---
## 📂 项目结构 (Project Structure)
```
├── config.py          # 全局配置文件（密钥、硬件加速提供者、PID核心参数）
├── main.py            # 主程序核心（视觉流、事件状态机、串口通信管理）
├── face_rec.py        # 视觉引擎（基于 DmlExecutionProvider 的显卡加速推理）
├── voice.py           # 语音大模型引擎（Qwen API 调用与本地音频播放状态锁）
├── notifier.py        # 网络通知模块（ImgBB图床上传与钉钉Webhook异步推送）
├── logger.py          # 数据持久化模块（CSV日志读写与本地周报文本生成）
├── requirements.txt   # 全局依赖环境清单
└── hardware/          
    └── sentinel_servo.ino  # 下位机 Arduino/ESP32 舵机平滑驱动源码 (C++)
```
    





