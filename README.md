# 🎥 Auto Video Translator & Dubber (AI 全自动视频翻译配音助手)


一个基于 Python 的全自动视频本地化工具。它能将外语视频自动识别、翻译、总结，并生成中文配音版本。支持**拖拽运行**和**后台监控**两种模式，完美支持长视频（自动分段处理）。

> **核心特性**：本地 Whisper 识别 + Qwen 大模型翻译 + 微软超自然语音合成 + FFmpeg 自动剪辑。

---

## ✨ 功能特性 (Features)

- **🎤 离线语音识别**: 集成 OpenAI Whisper 模型，精准提取视频语音（支持 GPU 加速）。
- **🧠 智能翻译与总结**: 调用 SiliconFlow (Qwen 2.5) API，提供高质量的中英翻译及视频内容总结笔记。
- **🗣️ AI 免费配音**: 使用 Microsoft Edge-TTS 生成自然流畅的中文旁白（支持云希/晓晓等音色）。
- **🎞️ 自动视频合成**: 使用 FFmpeg 自动替换视频音轨，生成最终的中文配音版视频。
- **🧩 长视频支持**: 独创的分段 TTS 合成算法，完美解决长视频配音中断问题（支持 1小时+ 视频）。

---

## 🛠️ 环境准备 (Prerequisites)

在运行本项目前，请确保安装以下环境：

1.  **Python 3.8+**: [下载 Python](https://www.python.org/downloads/)
2.  **FFmpeg** (必须): 用于音频处理和视频合成。
    *   [下载 Windows 构建版](https://www.gyan.dev/ffmpeg/builds/)
    *   **注意**: 请务必将 FFmpeg 的 `bin` 目录添加到系统的 `PATH` 环境变量中。
3.  **CUDA (可选)**: 如果你有 NVIDIA 显卡，建议安装 GPU 版本的 PyTorch 以获得 10x-50x 的加速体验。

---

## 📦 安装步骤 (Installation)

1.  **克隆仓库**
    ```bash
    git clone https://github.com/hua1232/AI-video-translate-lear.git
    cd AI-video-translate-lear
    ```

2.  **安装依赖**
    ```bash
    pip install openai-whisper requests watchdog edge-tts
    ```
    *建议安装 GPU 版 PyTorch (视显卡情况而定):*
    ```bash
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    ```

3.  **配置 API Key**
    打开 `ai4.py` 文件，找到配置区域，填入你的 Key：
    ```python
    # 配置区域
    SILICONFLOW_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"  # 你的 SiliconFlow API Key
    ```

---

## 🚀 使用方法 (Usage)

### 方式一：双击快捷方式运行脚本
1.  找到项目目录下的 `.bat` 启动脚本。
2.  将视频文件 (`.mp4`, `.mov`, `.mkv`) **拖拽**到input_videos文件夹上。
3.  程序开始处理。

### 方式二：监控模式 (挂机)
1.  直接运行脚本：
    ```bash
    python ai4.py
    ```
2.  程序会启动监控模式，监听 `input_videos` 文件夹。
3.  将视频文件放入 `input_videos` 文件夹，程序会自动排队处理。

---

## 📂 输出文件说明 (Output)

处理完成后，结果将保存在你配置的 `OUTPUT_FOLDER` 中：

| 文件类型 | 文件名示例 | 说明 |
| :--- | :--- | :--- |
| **中英字幕** | `demo.srt` | 翻译后的中文字幕（含时间轴） |
| **原文字幕** | `demo_en.srt` | Whisper 识别出的英文原始字幕 |
| **学习笔记** | `demo_总结.txt` | AI 生成的视频核心要点总结 |
| **配音视频** | `demo_中文配音.mp4` | **最终成品**：中文配音 + 原画视频 |

---


