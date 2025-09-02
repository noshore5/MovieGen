from pathlib import Path
import openai
import datetime
import os
from dotenv import load_dotenv
from glob import glob
import textwrap
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

def get_latest_scene_dir(static_dir="static"):
    scene_dirs = sorted(
        [d for d in glob(f"{static_dir}/scene_*") if os.path.isdir(d)],
        key=os.path.getmtime,
        reverse=True
    )
    return scene_dirs[0] if scene_dirs else None

def extract_original_quote(prompt_file):
    with open(prompt_file, encoding="utf-8") as f:
        content = f.read()
    start = content.find("ORIGINAL QUOTE:")
    if start == -1:
        return None
    start = content.find("-" * 40, start)
    if start == -1:
        return None
    start += 40
    # Find the next section marker (GENERATED VISUAL PROMPTS)
    end = content.lower().find("generated visual prompts", start)
    if end == -1:
        end = len(content)
    quote = content[start:end].strip()
    # Remove any leading/trailing quotes and whitespace
    if quote.startswith('"') and quote.endswith('"'):
        quote = quote[1:-1]
    return quote.strip()

def generate_speech_for_scene(scene_dir=None):
    """
    Generate text-to-speech audio for the quote in the specified scene directory.
    If no scene_dir is provided, uses the latest scene directory.
    """
    if not scene_dir:
        scene_dir = get_latest_scene_dir()
    
    if not scene_dir:
        raise RuntimeError("No scene directory found.")
    
    prompt_file = os.path.join(scene_dir, "tolkien_prompts.txt")
    
    if not os.path.exists(prompt_file):
        raise RuntimeError(f"No prompts file found at {prompt_file}")
    
    quote = extract_original_quote(prompt_file)
    if not quote:
        raise RuntimeError("No original quote found in scene prompts file.")

    speech_file_path = Path(f"{scene_dir}/speech.mp3")

    # Call the TTS model
    with openai.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="fable",   # Available voices: alloy, verse, aria, etc
        input=quote
    ) as response:
        response.stream_to_file(speech_file_path)

    print(f"Saved TTS to {speech_file_path}")

    # Get actual duration of speech.mp3 using ffprobe
    import subprocess, json
    def get_audio_duration(audio_file):
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                str(audio_file)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 10.0  # fallback

    total_duration = get_audio_duration(speech_file_path)

    # Split quote into readable chunks (4-8 words per chunk)
    def split_into_chunks(text, min_words=4, max_words=8):
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk_size = min(max_words, max(min_words, len(words) - i))
            chunk = words[i:i+chunk_size]
            chunks.append(" ".join(chunk))
            i += chunk_size
        return chunks

    srt_file_path = Path(f"{scene_dir}/speech.srt")
    chunks = split_into_chunks(quote, min_words=4, max_words=8)
    total_chunks = len(chunks)
    chunk_duration = total_duration / total_chunks if total_chunks > 0 else total_duration

    def format_time(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    srt_lines = []
    for idx, chunk in enumerate(chunks):
        start_time = idx * chunk_duration
        end_time = (idx + 1) * chunk_duration if idx < total_chunks - 1 else total_duration
        srt_lines.append(f"{idx+1}\n{format_time(start_time)} --> {format_time(end_time)}\n{chunk}\n")

    srt_content = "\n".join(srt_lines) + "\n"
    with open(srt_file_path, "w", encoding="utf-8", newline='\n') as srt_file:
        srt_file.write(srt_content)
    print(f"Saved subtitles to {srt_file_path}")
    return str(speech_file_path)
'''
# For backward compatibility when run as script
if __name__ == "__main__":
    # Find latest scene dir and prompt file
    scene_dir = get_latest_scene_dir()
    prompt_file = os.path.join(scene_dir, "tolkien_prompts.txt") if scene_dir else None
    quote = extract_original_quote(prompt_file) if prompt_file and os.path.exists(prompt_file) else None

    if not quote:
        raise RuntimeError("No original quote found in latest scene prompts file.")

    speech_file_path = Path(f"{scene_dir}/speech.mp3")

    # Call the TTS model
    with openai.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="verse",   # Available voices: alloy, verse, aria, etc
        input=quote
    ) as response:
        response.stream_to_file(speech_file_path)

    print(f"Saved TTS to {speech_file_path}")

    # Export SRT subtitle file (placeholder duration: 10 seconds)
    srt_file_path = Path(f"{scene_dir}/speech.srt")
    # Ensure LF line endings and blank line after last entry
    srt_content = f"1\n00:00:00,000 --> 00:00:10,000\n{quote}\n\n"
    #with open(srt_file_path, "w", encoding="utf-8", newline='\n') as srt_file:
    #    srt_file.write(srt_content)
    #print(f"Saved subtitles to {srt_file_path}")
    '''
    