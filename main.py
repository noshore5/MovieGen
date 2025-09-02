import os
import random
from datetime import datetime
import sys
import asyncio
sys.path.append('agents')
from promptgen import generateprompts, save_prompts_to_file
from imagegen import main as imagegen_main
from qts import generate_speech_for_scene

text = "At the edge of the village, the river Styx looks like any other stream. Until midnight, when coins float against the current, and voices beg you not to pick them up. Last night… you did."

async def main():
    # Read all quotes from file
    with open("makin_quotes.txt", encoding="utf-8") as f:
        quotes = [line.strip() for line in f if line.strip()]

    # Pick a random quote
    #quote = random.choice(quotes)
    quote = text
    # Create a short timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    scene_dir = os.path.join("static", f"scene_{timestamp}")
    os.makedirs(scene_dir, exist_ok=True)

    # Generate prompts using promptgen
    print(f"Generating prompts for quote: {quote[:50]}...")
    prompts = generateprompts(quote)

    # Save the quote and prompts in the new scene folder
    saved_file = save_prompts_to_file(quote, prompts, scene_dir)

    print(f"Scene created in: {scene_dir}")
    print(f"Prompts saved to: {saved_file}")
    print(f"Quote: {quote}")

    # Generate images using imagegen
    print("\nGenerating images...")
    await imagegen_main()

    # Generate speech for the quote
    print("\nGenerating speech...")
    try:
        speech_file = generate_speech_for_scene(scene_dir)
        print(f"Speech generated: {speech_file}")
    except Exception as e:
        print(f"Error generating speech: {e}")

    print(f"\nScene complete! All files saved to: {scene_dir}")

    # Run burns_ffmpeg to create video with Ken Burns effect and subtitles
    print("\nCreating video with Ken Burns effect and subtitles...")
    import subprocess
    burns_ffmpeg_path = os.path.join(os.path.dirname(__file__), 'agents', 'burns_ffmpeg.py')
    result = subprocess.run([sys.executable, burns_ffmpeg_path], cwd=os.getcwd())
    if result.returncode == 0:
        print("Video creation complete!")
    else:
        print(f"Error running burns_ffmpeg.py: {result}")

if __name__ == "__main__":
    asyncio.run(main())
