import os
import glob
from pathlib import Path

def get_latest_scene_dir(static_dir="static"):
    """Get the most recently created scene directory"""
    pattern = os.path.join(static_dir, "scene_*")
    scene_dirs = [d for d in glob.glob(pattern) if os.path.isdir(d)]
    if not scene_dirs:
        return None
    return max(scene_dirs, key=os.path.getmtime)

def create_simple_slideshow(scene_dir=None):
    """Create a simple HTML slideshow from images and audio in the scene directory"""
    
    # Get the latest scene directory if none provided
    if not scene_dir:
        scene_dir = get_latest_scene_dir()
    
    if not scene_dir:
        raise RuntimeError("No scene directory found")
    
    print(f"Creating slideshow from scene: {scene_dir}")
    
    # Check for audio file
    audio_file = os.path.join(scene_dir, "speech.mp3")
    has_audio = os.path.exists(audio_file)
    
    # Find images
    image_pattern = os.path.join(scene_dir, "*.png")
    image_files = glob.glob(image_pattern)
    
    if not image_files:
        raise RuntimeError(f"No PNG images found in {scene_dir}")
    
    # Sort images by creation time for consistent ordering
    image_files.sort(key=os.path.getmtime)
    print(f"Found {len(image_files)} images")
    
    # Create HTML slideshow
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tolkien Scene Slideshow</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: #f0f0f0;
            font-family: 'Times New Roman', serif;
            text-align: center;
        }}
        .slideshow-container {{
            position: relative;
            max-width: 800px;
            margin: auto;
            background: #2a2a2a;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        .slide {{
            display: none;
            position: relative;
        }}
        .slide.active {{
            display: block;
        }}
        .slide img {{
            width: 100%;
            height: 600px;
            object-fit: cover;
            transition: transform 10s ease-in-out;
        }}
        .slide.active img {{
            transform: scale(1.1);
        }}
        .controls {{
            margin: 20px 0;
        }}
        button {{
            background: #4a4a4a;
            color: #f0f0f0;
            border: none;
            padding: 10px 20px;
            margin: 0 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        button:hover {{
            background: #6a6a6a;
        }}
        .progress {{
            width: 100%;
            height: 4px;
            background: #3a3a3a;
            margin: 20px 0;
        }}
        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #ffd700, #ff8c00);
            width: 0%;
            transition: width 0.3s ease;
        }}
        .scene-info {{
            margin: 20px 0;
            padding: 20px;
            background: #2a2a2a;
            border-radius: 5px;
            max-width: 800px;
            margin: 20px auto;
        }}
    </style>
</head>
<body>
    <h1>🧙‍♂️ Tolkien Scene Slideshow</h1>
    
    <div class="scene-info">
        <p><strong>Scene:</strong> {os.path.basename(scene_dir)}</p>
        <p><strong>Images:</strong> {len(image_files)} generated scenes</p>
        {"<p><strong>Audio:</strong> Available</p>" if has_audio else "<p><strong>Audio:</strong> Not available</p>"}
    </div>
    
    <div class="slideshow-container">
"""

    # Add slides
    for i, img_path in enumerate(image_files):
        img_name = os.path.basename(img_path)
        active_class = "active" if i == 0 else ""
        html_content += f"""
        <div class="slide {active_class}">
            <img src="{img_name}" alt="Scene {i+1}">
        </div>
"""

    # Add controls and JavaScript
    html_content += f"""
    </div>
    
    <div class="controls">
        <button onclick="previousSlide()">⬅️ Previous</button>
        <button id="playBtn" onclick="toggleAutoplay()">▶️ Play</button>
        <button onclick="nextSlide()">Next ➡️</button>
    </div>
    
    <div class="progress">
        <div class="progress-bar" id="progressBar"></div>
    </div>

    {"<audio id='narration' src='speech.mp3' preload='auto'></audio>" if has_audio else ""}
    
    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        let isPlaying = false;
        let slideInterval;
        const slideDuration = 30000; // 30 seconds per slide if no audio
        
        function showSlide(n) {{
            slides[currentSlide].classList.remove('active');
            currentSlide = (n + totalSlides) % totalSlides;
            slides[currentSlide].classList.add('active');
            updateProgress();
        }}
        
        function nextSlide() {{
            showSlide(currentSlide + 1);
        }}
        
        function previousSlide() {{
            showSlide(currentSlide - 1);
        }}
        
        function toggleAutoplay() {{
            const playBtn = document.getElementById('playBtn');
            {"const audio = document.getElementById('narration');" if has_audio else ""}
            
            if (isPlaying) {{
                clearInterval(slideInterval);
                {"audio.pause();" if has_audio else ""}
                playBtn.textContent = '▶️ Play';
                isPlaying = false;
            }} else {{
                {"audio.play();" if has_audio else ""}
                {"const audioDuration = audio.duration * 1000;" if has_audio else "const audioDuration = " + str(len(image_files) * 30000) + ";"}
                const intervalTime = audioDuration / totalSlides;
                
                slideInterval = setInterval(nextSlide, intervalTime);
                playBtn.textContent = '⏸️ Pause';
                isPlaying = true;
            }}
        }}
        
        function updateProgress() {{
            const progress = (currentSlide / (totalSlides - 1)) * 100;
            document.getElementById('progressBar').style.width = progress + '%';
        }}
        
        // Keyboard controls
        document.addEventListener('keydown', function(e) {{
            switch(e.key) {{
                case 'ArrowLeft':
                    previousSlide();
                    break;
                case 'ArrowRight':
                    nextSlide();
                    break;
                case ' ':
                    e.preventDefault();
                    toggleAutoplay();
                    break;
            }}
        }});
        
        // Initialize progress
        updateProgress();
    </script>
</body>
</html>
"""

    # Save HTML file
    output_path = os.path.join(scene_dir, "slideshow.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Slideshow created successfully: {output_path}")
    return output_path

# For backward compatibility when run as script
if __name__ == "__main__":
    create_simple_slideshow()
