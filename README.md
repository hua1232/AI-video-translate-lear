这是一个基于 Python 的全自动视频本地化工具。它能够自动识别视频语音、翻译字幕、生成内容总结，甚至生成中文配音并合成到原视频中。支持文件夹监控和拖拽运行两种模式。
✨ 核心功能
🎤 离线语音识别: 使用 OpenAI Whisper 模型（本地运行，无需联网 API）提取视频语音。
🇨🇳 双语字幕翻译: 调用 SiliconFlow (Qwen 2.5) 大模型进行高质量中英翻译。
📝 智能总结笔记: 自动生成视频的核心主旨、关键点和结论笔记。
🗣️ AI 免费配音: 集成微软 Edge-TTS，生成自然流畅的中文旁白（支持长视频分段合成）。
🎞️ 自动视频合成: 使用 FFmpeg 自动将配音与原画合成，生成最终的中文配音版视频。
⚡ 双模式运行:
监控模式: 只要把视频丢进文件夹，后台自动处理。
拖拽模式: 把视频拖到图标上，立即开始处理。
🛠️ 环境依赖
在使用本项目之前，请确保你的电脑已安装以下环境：
Python 3.8+: 下载 Python
FFmpeg (必须): 用于音频提取和视频合成。
下载 FFmpeg
注意: 必须将 FFmpeg 的 bin 目录添加到系统的 PATH 环境变量中。
NVIDIA 显卡 (推荐): 建议安装 CUDA 版本的 PyTorch 以加速 Whisper 识别。
📦 安装步骤
克隆项目
code
Bash
git clone https://gitlab.com/your-username/your-project.git
cd your-project
安装 Python 依赖库
建议创建一个 requirements.txt 文件并运行安装：
code
Bash
pip install -r requirements.txt
(如果没有 requirements.txt，请运行以下命令):
code
Bash
pip install openai-whisper requests watchdog edge-tts
# 如果有 NVIDIA 显卡，请去 pytorch 官网安装 GPU 版本 torch
配置文件
打开主脚本文件（如 ai4.py），修改以下配置区域：
code
Python
# 配置 SiliconFlow API Key (必填)
SILICONFLOW_API_KEY = "sk-xxxxxxxxxxxxxx"

🚀 使用方法
双击运行启动脚本或直接运行 Python 代码：
code
Bash
python ai4.py
程序启动后会监听 input_videos 文件夹。
将需要翻译的视频放入 input_videos 文件夹中，程序会自动开始排队处理。
📂 输出文件说明
处理完成后，你将在输出目录（output_files）看到以下文件：
文件后缀	说明
_en.srt	识别出的英文原始字幕
.srt	翻译后的中文字幕
_总结.txt	AI 生成的视频学习笔记
_中文配音.mp4	最终成品：中文配音 + 原画视频
⚠️ 常见问题 (FAQ)
Q: 为什么提示 "Error opening input file"?
A: 这是 FFmpeg 路径问题。请确保代码中使用了 os.path.abspath 将路径转换为绝对路径（已修复）。
Q: 运行速度很慢？
A: 请检查日志中显示的是 Device: CPU 还是 CUDA。如果是 CPU，请尝试安装 GPU 版本的 PyTorch 或将 Whisper 模型设置为 base 或 tiny。
📜 许可证
本项目仅供学习和个人使用。
API 服务（SiliconFlow）和 TTS 服务（Microsoft）的使用请遵守相应服务商的条款。
