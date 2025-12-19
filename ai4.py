import os
import sys
import time
import shutil
import logging
import requests
import subprocess
import warnings
import asyncio
import re
import edge_tts
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 忽略警告
warnings.filterwarnings("ignore")

# ================= 配置区域 =================

# 1. 路径配置
INPUT_FOLDER = "./input_videos"
PROCESSED_FOLDER = "./processed_videos"
OUTPUT_FOLDER ="./output_files"

# 2. 翻译 API
SILICONFLOW_API_KEY = "sk-cgzltmbcjlnqhunrznvxhemvwywanpikoaweeuhhcitdzhbr"
MODEL_TRANSLATE = "Qwen/Qwen2.5-7B-Instruct"

# 3. Whisper 设置
WHISPER_MODEL_SIZE = "small"

# 4. 配音设置
TTS_VOICE = "zh-CN-YunxiNeural"
ENABLE_DUBBING = True

# 5. 支持格式
SUPPORTED_EXTENSIONS = ('.mp4', '.mov', '.avi', '.mkv', '.flv')

# ================= 初始化 =================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger()

logger.info("⏳ 正在加载 Whisper 模型...")
import whisper
try:
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(WHISPER_MODEL_SIZE, device=device)
    logger.info(f"✅ 模型加载完成 (设备: {device})")
except Exception as e:
    logger.error(f"❌ 模型加载失败: {e}")
    exit()

# ================= 核心函数 =================

def format_timestamp(seconds):
    millis = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

def transcribe_local(file_path):
    logger.info("2. 正在识别语音 (Whisper)...")
    try:
        result = model.transcribe(file_path, language="en")
        segments = result.get('segments', [])
        srt_content = ""
        for i, seg in enumerate(segments, 1):
            start = format_timestamp(seg['start'])
            end = format_timestamp(seg['end'])
            text = seg['text'].strip()
            srt_content += f"{i}\n{start} --> {end}\n{text}\n\n"
        return srt_content
    except Exception as e:
        logger.error(f"❌ 识别失败: {e}")
        return None

def split_text(text, max_chars=3000):
    if not text: return []
    blocks = text.strip().split('\n\n')
    chunks = []
    curr = []
    curr_len = 0
    for b in blocks:
        if curr_len + len(b) > max_chars:
            chunks.append("\n\n".join(curr))
            curr = []
            curr_len = 0
        curr.append(b)
        curr_len += len(b)
    if curr: chunks.append("\n\n".join(curr))
    return chunks

def translate_srt(full_srt):
    logger.info("3. 正在翻译字幕 (Qwen)...")
    if not full_srt: return ""
    chunks = split_text(full_srt)
    final = ""
    for i, chunk in enumerate(chunks):
        logger.info(f"   🔄 翻译片段 {i+1}/{len(chunks)}...")
        url = "https://api.siliconflow.cn/v1/chat/completions"
        headers = {"Authorization": f"Bearer {SILICONFLOW_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": MODEL_TRANSLATE,
            "messages": [
                {"role": "system", "content": "你是一个专业的字幕翻译引擎。直接输出中文翻译，保持SRT格式，不要解释，不要修改时间轴。"},
                {"role": "user", "content": chunk}
            ],
            "stream": False, "temperature": 0.3
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=60)
            if res.status_code == 200:
                final += res.json()['choices'][0]['message']['content'] + "\n\n"
        except Exception:
            pass
    return final

def extract_plain_text(srt_text):
    lines = srt_text.strip().split('\n')
    text_only = []
    for line in lines:
        if line.strip() and not line.isdigit() and '-->' not in line:
            text_only.append(line.strip())
    return "，".join(text_only)

def generate_summary(text):
    logger.info("6. 正在生成精炼总结 (Qwen)...")
    if not text: return None
    # 截取文本，防止 token 溢出
    if len(text) > 4000: text = text[:4000]
    
    # ★★★ 修改核心：加入严格的字数限制和精简指令 ★★★
    prompt = f"""你是一个极其高效的专业内容分析师。请阅读字幕，生成一份**高浓缩、快节奏**的专业总结。
    
    【严格限制】：
    1. **字数限制**：全篇总结必须严格控制在 **350字以内**。
    2. **拒绝废话**：不要任何铺垫（如“这段视频主要讲了...”），直接上干货。
    3. **语言风格**：专业、犀利、简练。

    【输出格式】：
    ### 🎯 核心主旨 (1句话)
    (用最精炼的语言概括视频核心，不超过50字)

    ### 💡 关键知识点 (仅限3条)
    *   **关键词1**：一句话原理解析。
    *   **关键词2**：一句话原理解析。
    *   **关键词3**：一句话原理解析。

    ### 📝 结论 (1句话)
    (最终的结论或启示)

    字幕内容：
    {text}"""
    
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {SILICONFLOW_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL_TRANSLATE,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, 
        "temperature": 0.3, # 温度调低，让AI更听话，不发散
        "max_tokens": 500   # 物理强制限制输出长度（防止AI啰嗦）
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"❌ 总结生成失败: {e}")
    return None

def get_duration(file_path):
    """使用 ffprobe 获取文件时长(秒)"""
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    try:
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        return float(output)
    except Exception:
        return 0.0
    
def merge_video(v_path, a_path, out_path):
    logger.info("7. 正在进行智能视频合成...")
    v_path, a_path, out_path = map(os.path.abspath, [v_path, a_path, out_path])
    
    # 1. 获取时长
    dur_video = get_duration(v_path)
    dur_audio = get_duration(a_path)
    
    logger.info(f"   - 视频时长: {dur_video:.2f}秒")
    logger.info(f"   - 配音时长: {dur_audio:.2f}秒")
    
    # 2. 判断逻辑
    if dur_audio > dur_video:
        # === 情况 A：配音太长了，需要加速 ===
        speed_factor = dur_audio / dur_video
        # 限制最大加速倍数，防止声音听不清（比如限制在 2.0 倍以内）
        if speed_factor > 2.0:
            logger.warning(f"   ⚠️ 配音比视频长太多 ({speed_factor:.2f}倍)，强制加速可能导致听感不佳")
            speed_factor = 2.0
            
        logger.info(f"   🚀 检测到配音超时，将自动加速 {speed_factor:.2f} 倍以匹配视频...")
        
        # 使用 atempo 滤镜加速音频 (atempo 范围 0.5 - 2.0)
        # 如果需要更高倍速，需要级联，这里简化处理只支持到 2.0
        cmd = f'ffmpeg -i "{v_path}" -i "{a_path}" -filter_complex "[1:a]atempo={speed_factor}[a]" -map 0:v:0 -map "[a]" -shortest "{out_path}" -y -loglevel error'
        
    else:
        # === 情况 B：配音比视频短 (正常情况) ===
        # 不做拉伸（否则会变慢动作怪兽音），直接保留原画，音频播完后静音
        logger.info(f"   ✅ 配音时长在正常范围内，保持原速合成...")
        cmd = f'ffmpeg -i "{v_path}" -i "{a_path}" -c:v copy -map 0:v:0 -map 1:a:0 "{out_path}" -y -loglevel error'

    try:
        subprocess.run(cmd, shell=True, check=True)
        logger.info(f"🎉 完成: {out_path}")
    except subprocess.CalledProcessError:
        logger.error("❌ 视频合成失败")

def save_file(content, path):
    with open(path, "w", encoding="utf-8-sig") as f: f.write(content)


# ★★★ 新增：长视频配音核心函数 ★★★
async def generate_dubbing_for_long_video(srt_text, base_name):
    """分段生成TTS并合并，专门处理长视频"""
    logger.info("5. 正在处理长视频配音...")
    
    # 1. 解析SRT
    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)', re.DOTALL)
    srt_entries = [m.groups() for m in pattern.finditer(srt_text)]
    if not srt_entries: return None

    # 2. 分块并生成TTS
    chunk_size = 20 # 每20句字幕合并成一个TTS请求
    temp_audio_files = []
    
    for i in range(0, len(srt_entries), chunk_size):
        chunk = srt_entries[i:i+chunk_size]
        chunk_text = "，".join([entry[3].replace('\n', ' ') for entry in chunk])
        
        if not chunk_text.strip(): continue
        
        temp_audio_path = os.path.join(OUTPUT_FOLDER, f"temp_{base_name}_{i//chunk_size}.mp3")
        logger.info(f"   🔄 生成配音片段 {i//chunk_size + 1}...")
        
        try:
            communicate = edge_tts.Communicate(chunk_text, TTS_VOICE)
            await communicate.save(temp_audio_path)
            temp_audio_files.append(temp_audio_path)
        except Exception as e:
            logger.error(f"   ❌ TTS片段生成失败: {e}")
            continue

    if not temp_audio_files:
        logger.error("❌ 所有TTS片段均生成失败，无法继续。")
        return None

    # 3. 合并所有TTS片段
    logger.info("   - 正在合并所有配音片段...")
    concat_list_path = os.path.join(OUTPUT_FOLDER, "concat_list.txt")
    with open(concat_list_path, 'w', encoding='utf-8') as f:
        for audio_file in temp_audio_files:
            # FFmpeg concat demuxer 需要特定的格式，且路径中的反斜杠要处理
            f.write(f"file '{os.path.abspath(audio_file).replace(os.sep, '/')}'\n")

    final_audio_path = os.path.join(OUTPUT_FOLDER, f"final_dub_{base_name}.mp3")
    cmd_concat = f'ffmpeg -f concat -safe 0 -i "{concat_list_path}" -c copy "{final_audio_path}" -y -loglevel error'
    
    try:
        subprocess.run(cmd_concat, shell=True, check=True)
        logger.info("   ✅ 所有配音片段合并成功！")
    except subprocess.CalledProcessError:
        logger.error("   ❌ FFmpeg合并音频失败。")
        final_audio_path = None # 标记失败
    
    # 4. 清理临时文件
    os.remove(concat_list_path)
    for f in temp_audio_files:
        if os.path.exists(f): os.remove(f)
        
    return final_audio_path

# ★★★ 主处理流程 ★★★
async def process_single_video(filepath):
    filename = os.path.basename(filepath)
    base_name = os.path.splitext(filename)[0]
    logger.info(f"\n{'='*40}\n🎬 开始处理: {filename}")

    # 1. 识别
    en_srt = transcribe_local(filepath)
    if not en_srt: return
    save_file(en_srt, os.path.join(OUTPUT_FOLDER, f"{base_name}_en.srt"))

    # 2. 翻译
    cn_srt = translate_srt(en_srt)
    if not cn_srt: return
    save_file(cn_srt, os.path.join(OUTPUT_FOLDER, f"{base_name}.srt"))

    # 3. 提取纯文本用于总结
    cn_pure_text = extract_plain_text(cn_srt)

    # 4. 生成总结
    summary_note = generate_summary(cn_pure_text)
    if summary_note:
        save_file(summary_note, os.path.join(OUTPUT_FOLDER, f"{base_name}_总结.txt"))
        logger.info(f"📝 总结笔记已生成")

    # 5. 配音 & 合成
    if ENABLE_DUBBING:
        # 调用新的长视频处理函数
        final_dub_audio = await generate_dubbing_for_long_video(cn_srt, base_name)
        
        if final_dub_audio:
            out_video = os.path.join(OUTPUT_FOLDER, f"{base_name}_中文配音.mp4")
            merge_video(filepath, final_dub_audio, out_video)
            # 清理最终合并的音频
            if os.path.exists(final_dub_audio): os.remove(final_dub_audio)

    # 6. 归档
    if os.path.abspath(filepath).startswith(os.path.abspath(INPUT_FOLDER)):
        if os.path.exists(filepath):
            shutil.move(filepath, os.path.join(PROCESSED_FOLDER, filename))
            logger.info("📦 源文件已归档")

# ================= 入口逻辑 =================

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(SUPPORTED_EXTENSIONS):
            size = -1
            while size != os.path.getsize(event.src_path):
                size = os.path.getsize(event.src_path)
                time.sleep(1)
            asyncio.run(process_single_video(event.src_path))

if __name__ == "__main__":
    for f in [INPUT_FOLDER, OUTPUT_FOLDER, PROCESSED_FOLDER]:
        if not os.path.exists(f): os.makedirs(f)

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path) and file_path.lower().endswith(SUPPORTED_EXTENSIONS):
            asyncio.run(process_single_video(file_path))
            logger.info("\n✅ 处理完毕！请按任意键退出...")
            input()
        else:
            logger.error("❌ 错误：请拖入支持的视频文件")
            input()
    else:
        logger.info("🚀 监控模式已启动")
        logger.info(f"📂 监听: {os.path.abspath(INPUT_FOLDER)}")
        observer = Observer()
        observer.schedule(VideoHandler(), INPUT_FOLDER, recursive=False)
        observer.start()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()