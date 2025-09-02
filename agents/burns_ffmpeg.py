import subprocess
import os
import glob
import json
import random


import requests
import random
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("JAMENDO_CLIENT")
if not CLIENT_ID:
    raise ValueError("JAMENDO_CLIENT not found in .env file")




def get_audio_duration(audio_file):
    """Get the duration of an audio file in seconds using ffprobe"""
    try:
        cmd = [
            "ffprobe", 
            "-v", "quiet", 
            "-print_format", "json", 
            "-show_format", 
            audio_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 30.0  # fallback to 30 seconds

def get_image_files(image_folder):
    """Get sorted list of beat image files"""
    pattern = os.path.join(image_folder, "beat_*.png")
    images = sorted(glob.glob(pattern))
    return images

def generate_random_zoompan(duration_frames):
    """Generate random zoompan parameters for Ken Burns effect"""
    # Random zoom start and end values
    zoom_start = random.uniform(1.0, 1.4)
    zoom_end = random.uniform(1.2, 1.5)
    
    # 50% chance to reverse zoom direction (zoom out instead of in)
    if random.choice([True, False]):
        zoom_start, zoom_end = zoom_end, zoom_start
    
    # Random pan start position (x,y coordinates from 0-1)
    x_start = random.uniform(0, 0.3)
    y_start = random.uniform(0, 0.3)
    
    # Random pan end position
    x_end = random.uniform(0, 0.3)
    y_end = random.uniform(0, 0.3)
    
    # Ensure some movement
    if abs(x_end - x_start) < 0.1:
        x_end = x_start + (0.2 if random.choice([True, False]) else -0.2)
        x_end = max(0, min(0.3, x_end))
    
    if abs(y_end - y_start) < 0.1:
        y_end = y_start + (0.2 if random.choice([True, False]) else -0.2)
        y_end = max(0, min(0.3, y_end))
    
    # Create zoompan filter with random easing
    easing_types = ['', 'in', 'out', 'in_out']
    easing = random.choice(easing_types)
    
    # Build the zoompan expression
    zoom_expr = f"'if(lte(on,1),{zoom_start},{zoom_start}+({zoom_end}-{zoom_start})*pow((on-1)/({duration_frames}-1),2))'"
    x_expr = f"'{x_start}+({x_end}-{x_start})*pow(on/{duration_frames},1.5)'"
    y_expr = f"'{y_start}+({y_end}-{y_start})*pow(on/{duration_frames},1.5)'"
    
    # Set output size to match input images (vertical mobile: 768x1280)
    zoompan_filter = f"zoompan=z={zoom_expr}:x=iw*{x_expr}:y=ih*{y_expr}:d={duration_frames}:s=768x1280"
    
    print(f"  Zoom: {zoom_start:.2f}→{zoom_end:.2f}, Pan: ({x_start:.2f},{y_start:.2f})→({x_end:.2f},{y_end:.2f})")
    
    return zoompan_filter

# ------------------------------
# CONFIGURATION
# ------------------------------
frame_rate = 1                 # frames per second for images (1 image = 1 second)
zoom = 1.1                     # Ken Burns zoom factor
# Find the latest scene path by timestamp

scene_dirs = glob.glob('./static/scene_*/')
if scene_dirs:
    latest_scene = max(scene_dirs, key=os.path.getmtime)
    scene_path = latest_scene
else:
    scene_path = None

# Set image folder and audio file based on scene_path
if scene_path:
    image_folder = scene_path
    audio_file = os.path.join(scene_path, "speech.mp3")
    output_file = os.path.join(scene_path, "movie.mp4")
else:
    image_folder = "./static/"  # fallback to static folder if no scene found
    audio_file = "narration.mp3"   # fallback audio file
    output_file = "movie.mp4"

def fetch_jamendo_track():
    # Fetch tracks
      # Tag to filter tracks
    instrumental = True                # Only instrumental tracks
    licenses = ["by", "cc0"] 
    limit = 10
    licenses_str = ",".join(licenses)
    tags = ["ambient", "cinematic"]
    tags_str = ",".join(tags)

    instrumental_str = "true" if instrumental else "false"

    url = (
    f"https://api.jamendo.com/v3.0/tracks/?client_id={CLIENT_ID}"
    f"&format=json&limit={limit}&license={licenses_str}&include=musicinfo&instrumental={instrumental_str}&tags={tags_str}"
    )

    response = requests.get(url)
    data = response.json()

    tracks = data['results']
    track = random.choice(tracks)

    # Download the track
    audio_url = track['audio']
    r = requests.get(audio_url)
    filename = os.path.join(scene_path, f"music_{track['name']}.mp3")
    with open(filename, "wb") as f:
        f.write(r.content)

    print(f"Downloaded '{track['name']}' to {filename} by {track['artist_name']} ({track['license_ccurl']})")

fetch_jamendo_track()

# ------------------------------
# CALCULATE TIMING AND CREATE INDIVIDUAL CLIPS
# ------------------------------
image_files = get_image_files(image_folder)
num_images = len(image_files)

if num_images == 0:
    print("No images found!")
    exit(1)

audio_duration = get_audio_duration(audio_file)
time_per_image = audio_duration / num_images

print(f"Audio duration: {audio_duration:.2f}s")
print(f"Number of images: {num_images}")
print(f"Time per image: {time_per_image:.2f}s")

# Calculate frame rate and duration for ffmpeg
fps = 25  # output video fps
frames_per_image = int(time_per_image * fps)

print(f"Frames per image: {frames_per_image}")
print("\nGenerating individual clips with random effects:")

# Create temporary clips for each image
temp_clips = []
for i, image_file in enumerate(image_files):
    print(f"\nProcessing image {i+1}/{num_images}: {os.path.basename(image_file)}")
    
    # Generate random zoompan effect
    zoompan_filter = generate_random_zoompan(frames_per_image)
    
    # Create temporary output filename
    temp_clip = os.path.join(image_folder, f"temp_clip_{i+1:02d}.mp4")
    temp_clips.append(temp_clip)
    
    # FFmpeg command for individual clip
    cmd = [
        "ffmpeg",
        "-y",  # overwrite output
        "-loop", "1",  # loop the single image
        "-i", image_file,
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-vf", f"{zoompan_filter},fps={fps}",
        "-t", str(time_per_image),  # duration of this clip
        temp_clip
    ]
    
    print(f"  Creating clip: {os.path.basename(temp_clip)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Error creating clip: {result.stderr}")

print(f"\nConcatenating {len(temp_clips)} clips with audio...")

# Verify all temp clips were created successfully
missing_clips = []
for clip in temp_clips:
    if not os.path.exists(clip):
        missing_clips.append(clip)

if missing_clips:
    print(f"❌ Missing clips: {missing_clips}")
    print("Cannot proceed with concatenation")
    exit(1)

# Create concat file list with proper Windows paths
concat_file = os.path.join(image_folder, "concat_list.txt")
with open(concat_file, 'w') as f:
    for clip in temp_clips:
        # Use absolute paths to avoid path issues
        abs_clip_path = os.path.abspath(clip)
        f.write(f"file '{abs_clip_path}'\n")

print(f"Created concat file: {concat_file}")

# Step 1: Concatenate video clips (no audio)
temp_video = os.path.join(image_folder, "temp_video.mp4")
cmd_concat = [
    "ffmpeg",
    "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", os.path.abspath(concat_file),
    "-c:v", "libx264",
    "-preset", "fast",
    "-pix_fmt", "yuv420p",
    temp_video
]
print("\nConcatenating video clips (no audio)...")
print("Command:", " ".join(cmd_concat))
result_concat = subprocess.run(cmd_concat, capture_output=True, text=True)
if result_concat.returncode != 0:
    print(f"❌ Concatenation failed: {result_concat.stderr}")
    print(f"stdout: {result_concat.stdout}")
    exit(1)
if not os.path.exists(temp_video):
    print(f"❌ temp_video.mp4 was not created at {temp_video}")
    exit(1)
print(f"✅ Concatenation successful: {temp_video}")

# Step 2: Add audio to the concatenated video
print("Adding audio to video...")
def is_audio_silent(audio_file):
    """Check if the audio file is silent (duration 0 or very low volume) using ffmpeg/ffprobe."""
    # Check duration
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        if duration == 0:
            return True
    except Exception:
        return True

    # Check volume (mean_volume)
    try:
        cmd = [
            "ffmpeg",
            "-i", audio_file,
            "-af", "volumedetect",
            "-f", "null", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        for line in result.stderr.splitlines():
            if "mean_volume" in line:
                parts = line.split('mean_volume:')
                if len(parts) > 1:
                    mean_vol = float(parts[1].split()[0].replace('dB',''))
                    if mean_vol < -60:  # threshold for silence
                        return True
        return False
    except Exception:
        return False

if is_audio_silent(audio_file):
    print(f"❌ Audio file '{audio_file}' is silent or invalid. Skipping muxing.")
    exit(1)
if not os.path.exists(audio_file):
    print(f"❌ Audio file not found: {audio_file}")
    exit(1)
cmd_audio = [
    "ffmpeg",
    "-y",
    "-i", temp_video,
    "-i", audio_file,
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "128k",
    "-ac", "2",         # Force stereo
    "-ar", "44100",     # Force 44.1kHz sample rate
    "-shortest",
    output_file
]
print("Audio command:", " ".join(cmd_audio))
result_audio = subprocess.run(cmd_audio, capture_output=True, text=True)

if result_audio.returncode == 0:
    print(f"\n✅ Slideshow created successfully: {output_file}")
    # Verify the final video has audio
    print("Verifying audio in final video...")
    verify_cmd = [
        "ffprobe",
        "-v", "quiet",
        "-select_streams", "a",
        "-show_entries", "stream=codec_name,duration",
        "-of", "csv=p=0",
        output_file
    ]
    verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
    if verify_result.returncode == 0 and verify_result.stdout.strip():
        print(f"✅ Audio verified: {verify_result.stdout.strip()}")
    else:
        print("⚠️ Audio stream not detected in final video")

    # Step 3: Burn in subtitles from speech.srt if present

    srt_file = os.path.join(image_folder, "speech.srt")
    subtitled_output = os.path.join(image_folder, "movie_subtitled.mp4")
    if os.path.exists(srt_file):
        # Fix for Windows: use absolute path and forward slashes for ffmpeg subtitles filter
        abs_srt = os.path.abspath(srt_file).replace('\\', '/')
        # Escape colon after drive letter (Windows quirk for ffmpeg subtitles filter)
        if abs_srt[1:3] == ':/':
            abs_srt = abs_srt[0] + '\\:' + abs_srt[2:]
        # Wrap path in single quotes for ffmpeg filter
        filter_arg = f"subtitles='{abs_srt}'"
        print(f"Adding subtitles from {abs_srt} to video...")
        cmd_sub = [
            "ffmpeg",
            "-y",
            "-i", output_file,
            "-vf", filter_arg,
            "-c:a", "copy",
            subtitled_output
        ]
        print("Subtitle command:", " ".join(cmd_sub))
        result_sub = subprocess.run(cmd_sub, capture_output=True, text=True)
        if result_sub.returncode == 0:
            print(f"✅ Subtitled video created: {subtitled_output}")
        else:
            print(f"❌ Error adding subtitles: {result_sub.stderr}")
            print(f"stdout: {result_sub.stdout}")
    else:
        print(f"No subtitle file found at {srt_file}, skipping subtitle burn-in.")

    # Step 4: Add background music (music_*.mp3) trimmed to speech.mp3 duration
    import glob
    music_files = glob.glob(os.path.join(image_folder, "music_*.mp3"))
    if music_files:
        music_file = music_files[0]  # Use the first music file found
        print(f"Adding background music: {music_file}")
        # Get duration of speech.mp3
        speech_duration = get_audio_duration(audio_file)
        trimmed_music = os.path.join(image_folder, "music_trimmed.mp3")
        # Trim music to match speech.mp3 duration
        trim_cmd = [
            "ffmpeg", "-y",
            "-i", music_file,
            "-ss", "0",
            "-t", str(speech_duration),
            "-acodec", "copy",
            trimmed_music
        ]
        print("Trimming music command:", " ".join(trim_cmd))
        trim_result = subprocess.run(trim_cmd, capture_output=True, text=True)
        if trim_result.returncode != 0:
            print(f"❌ Error trimming music: {trim_result.stderr}")
        else:
            print(f"✅ Trimmed music created: {trimmed_music}")
            # Mix trimmed music with movie_subtitled.mp4 (speech+music)
            final_output = os.path.join(image_folder, "movie_final.mp4")
            mix_cmd = [
                "ffmpeg", "-y",
                "-i", subtitled_output,
                "-i", trimmed_music,
                "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[aout]",
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                final_output
            ]
            print("Mixing music command:", " ".join(mix_cmd))
            mix_result = subprocess.run(mix_cmd, capture_output=True, text=True)
            if mix_result.returncode == 0:
                print(f"✅ Final video with background music: {final_output}")
            else:
                print(f"❌ Error mixing music: {mix_result.stderr}")
                print(f"stdout: {mix_result.stdout}")

    # Clean up temporary files
    print("Cleaning up temporary files...")
    for temp_clip in temp_clips:
        if os.path.exists(temp_clip):
            os.remove(temp_clip)
    #if os.path.exists(temp_video):
        #os.remove(temp_video)
    if os.path.exists(concat_file):
        os.remove(concat_file)
    print("✅ Cleanup complete!")
else:
    print(f"❌ Error creating final video: {result_audio.stderr}")
    print(f"stdout: {result_audio.stdout}")
    print("Temporary files left for debugging")
