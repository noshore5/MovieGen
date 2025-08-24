import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
import base64
import os
import uuid
import glob
from datetime import datetime
from dotenv import load_dotenv

class RunwareImageGenerator:
    def __init__(self, api_key: str):
        load_dotenv()
        self.api_key = os.getenv("RUNWARE_API_KEY") if api_key is None else api_key
        self.base_url = "https://api.runware.ai/v1"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 768,
        height: int = 1280,
        steps: int = 20,
        guidance_scale: float = 7.5,
        model: str = "runware:100@1",
        output_format: str = "PNG"
    ) -> Dict[str, Any]:
        """
        Generate an image using the Runware API
        
        Args:
            prompt: Text description of the image to generate
            negative_prompt: What to avoid in the image
            width: Image width in pixels
            height: Image height in pixels
            steps: Number of inference steps
            guidance_scale: How closely to follow the prompt
            model: Model to use for generation
            output_format: Output format (PNG, JPEG, WEBP)
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Generate proper UUIDv4 for taskUUID
        payload = [
            {
                "taskType": "imageInference",
                "taskUUID": str(uuid.uuid4()),
                "positivePrompt": prompt,
                "model": model,
                "width": width,
                "height": height,
                "steps": steps,
                "CFGScale": guidance_scale,
                "outputFormat": output_format.lower(),
                "outputType": "base64Data",
                "numberOfImages": 1
            }
        ]
        
        if negative_prompt:
            payload[0]["negativePrompt"] = negative_prompt
        
        try:
            async with self.session.post(
                f"{self.base_url}/image/inference",
                headers=headers,
                json=payload
            ) as response:
                response_text = await response.text()
                
                if response.status != 200:
                    raise Exception(f"API returned status {response.status}: {response_text}")
                
                result = json.loads(response_text)
                return result
        
        except aiohttp.ClientError as e:
            raise Exception(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse API response: {str(e)}")
    
    async def save_image(self, base64_data: str, filepath: str) -> str:
        """
        Save base64 image data to file
        
        Args:
            base64_data: Base64 encoded image data
            filepath: Path where to save the image
        """
        try:
            # Remove data URL prefix if present
            if base64_data.startswith('data:'):
                base64_data = base64_data.split(',')[1]
            
            image_data = base64.b64decode(base64_data)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            return filepath
        
        except Exception as e:
            raise Exception(f"Failed to save image: {str(e)}")
    
    async def generate_and_save(
        self,
        prompt: str,
        output_path: str,
        **kwargs
    ) -> str:
        """
        Generate an image and save it to file
        
        Args:
            prompt: Text description of the image
            output_path: Where to save the generated image
            **kwargs: Additional parameters for image generation
        """
        result = await self.generate_image(prompt, **kwargs)
        
        # Updated to handle array response
        if isinstance(result, list) and len(result) > 0:
            image_data = result[0]
            if "imageBase64Data" in image_data:
                return await self.save_image(image_data["imageBase64Data"], output_path)
        elif "data" in result and len(result["data"]) > 0:
            image_data = result["data"][0]
            if "imageBase64Data" in image_data:
                return await self.save_image(image_data["imageBase64Data"], output_path)
        
        raise Exception(f"No image data received from API. Response: {result}")

# Convenience function for quick image generation
async def generate_tolkien_image(
    prompt: str,
    api_key: str,
    output_path: str,
    tolkien_style: bool = True
) -> str:
    """
    Generate a Tolkien-themed image
    
    Args:
        prompt: Base prompt for the image
        api_key: Runware API key
        output_path: Where to save the image
        tolkien_style: Whether to add Tolkien-style elements to prompt
    """
    if tolkien_style:
        enhanced_prompt = f"{prompt}, in the style of J.R.R. Tolkien, fantasy art, detailed, epic, cinematic lighting"
        negative_prompt = "modern, contemporary, urban, technology, cars, phones"
    else:
        enhanced_prompt = prompt
        negative_prompt = None
    
    async with RunwareImageGenerator(api_key) as generator:
        return await generator.generate_and_save(
            enhanced_prompt,
            output_path,
            negative_prompt=negative_prompt,
            width=768,  # Vertical mobile aspect ratio, valid multiple of 64
            height=1280,
            steps=30,
            guidance_scale=8.0
        )

# Function to parse structured scene format and generate images for each beat
async def generate_tolkien_scene_beats(
    scene_text: str,
    api_key: str,
    base_output_dir: str = "./static"
) -> List[str]:
    """
    Parse structured scene text and generate images for each visual beat
    
    Args:
        scene_text: Structured text containing scene context and visual beats
        api_key: Runware API key
        base_output_dir: Base directory for saving generated images
        
    Returns:
        List of file paths to generated images
    """
    import re
    
    generated_images = []
    
    # Extract visual beats from the text - new standardized format
    # Pattern for format: "**PROMPT_1:** [prompt text]"
    beat_pattern = r'\*\*PROMPT_\d+:\*\*\s*(.*?)(?=\n\s*\*\*PROMPT_\d+:|\n\s*$|$)'
    matches = re.findall(beat_pattern, scene_text, re.DOTALL | re.MULTILINE)
    
    # Clean up prompts and filter out empty ones
    beats = []
    for match in matches:
        clean_beat = match.strip()
        if clean_beat:
            # Remove any brackets and clean up formatting
            clean_beat = re.sub(r'^\[.*?\]\s*', '', clean_beat)
            clean_beat = re.sub(r'\n+', ' ', clean_beat)
            clean_beat = ' '.join(clean_beat.split())
            if clean_beat:
                beats.append(clean_beat)
    
    if not beats:
        # Fallback: try old format patterns
        old_beat_pattern = r'\*\*Beat \d+:.*?\*\*\s*\n\s*\*\s*\*\*Prompt:\*\*\s*"(.*?)"'
        beats = re.findall(old_beat_pattern, scene_text, re.DOTALL | re.IGNORECASE)
        
        if not beats:
            # Second fallback: simpler pattern to find prompts after **Prompt:** with quotes
            prompt_pattern = r'\*\*Prompt:\*\*\s*"(.*?)"'
            beats = re.findall(prompt_pattern, scene_text, re.DOTALL | re.IGNORECASE)
    
    # Debug: print what we found
    print(f"Debug: Raw beats found: {len(beats)}")
    for i, beat in enumerate(beats[:3], 1):  # Show first 3 beats
        print(f"Beat {i} preview: {beat[:100]}...")
    
    print(f"Found {len(beats)} beats in the scene text")
    
    if not beats:
        print("No beats found. Scene text preview:")
        print(scene_text[:500] + "..." if len(scene_text) > 500 else scene_text)
        return []
    
    # Debug: print first beat prompt
    print(f"First beat prompt preview: {beats[0][:100]}...")
    
    async with RunwareImageGenerator(api_key) as generator:
        for i, beat_prompt in enumerate(beats, 1):
            try:
                # Clean up the prompt text
                clean_prompt = beat_prompt.strip()
                # Remove any remaining markdown formatting
                clean_prompt = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_prompt)
                clean_prompt = re.sub(r'\*([^*]+)\*', r'\1', clean_prompt)
                
                # Validate prompt length
                if len(clean_prompt) < 2:
                    print(f"✗ Beat {i} prompt too short ({len(clean_prompt)} chars): {clean_prompt}")
                    continue
                elif len(clean_prompt) > 3000:
                    print(f"✗ Beat {i} prompt too long ({len(clean_prompt)} chars), truncating...")
                    clean_prompt = clean_prompt[:2900]  # Leave room for enhancement
                
                print(f"Beat {i} prompt length: {len(clean_prompt)} chars")
                
                # Generate filename
                beat_filename = f"beat_{i:02d}.png"
                output_path = os.path.join(base_output_dir, beat_filename)
                
                print(f"Generating Beat {i}: {beat_filename}")
                
                # Enhance prompt with Tolkien style
                enhanced_prompt = f"{clean_prompt}, in the style of J.R.R. Tolkien, fantasy art, detailed, epic, cinematic lighting, high detail"
                negative_prompt = "modern, contemporary, urban, technology, cars, phones, low quality, blurry, ugly"
                
                print(f"Final enhanced prompt length: {len(enhanced_prompt)} chars")
                
                # Generate and save image
                result = await generator.generate_image(
                    prompt=enhanced_prompt,
                    negative_prompt=negative_prompt,
                    width=768,  # Vertical mobile aspect ratio, valid multiple of 64
                    height=1280,
                    steps=35,
                    guidance_scale=8.5
                )
                
                # Save the image
                if isinstance(result, list) and len(result) > 0:
                    image_data = result[0]
                    if "imageBase64Data" in image_data:
                        saved_path = await generator.save_image(image_data["imageBase64Data"], output_path)
                        generated_images.append(saved_path)
                        print(f"✓ Beat {i} saved to: {saved_path}")
                elif "data" in result and len(result["data"]) > 0:
                    image_data = result["data"][0]
                    if "imageBase64Data" in image_data:
                        saved_path = await generator.save_image(image_data["imageBase64Data"], output_path)
                        generated_images.append(saved_path)
                        print(f"✓ Beat {i} saved to: {saved_path}")
                else:
                    print(f"✗ No image data received for Beat {i}")
                    
            except Exception as e:
                print(f"✗ Error generating Beat {i}: {e}")
                continue
    
    print(f"\nGenerated {len(generated_images)} images successfully!")
    return generated_images

def get_latest_scene_dir(static_dir: str = "static") -> Optional[str]:
    """
    Get the most recent scene directory from the static folder
    
    Args:
        static_dir: Directory containing the scene folders
        
    Returns:
        Path to the latest scene directory, or None if not found
    """
    pattern = os.path.join(static_dir, "scene_*")
    scene_dirs = [d for d in glob.glob(pattern) if os.path.isdir(d)]
    
    if not scene_dirs:
        return None
    
    # Sort by modification time, most recent first
    scene_dirs.sort(key=os.path.getmtime, reverse=True)
    return scene_dirs[0]

def get_latest_prompt_file(static_dir: str = "static") -> Optional[str]:
    """
    Get the tolkien_prompts file from the most recent scene directory
    
    Args:
        static_dir: Directory containing the scene folders
        
    Returns:
        Path to the prompt file, or None if not found
    """
    # First try to find the latest scene directory
    latest_scene_dir = get_latest_scene_dir(static_dir)
    if latest_scene_dir:
        prompt_file = os.path.join(latest_scene_dir, "tolkien_prompts.txt")
        if os.path.exists(prompt_file):
            return prompt_file
    
    # Fallback: look for prompt file directly in static
    filepath = os.path.join(static_dir, "tolkien_prompts.txt")
    if os.path.exists(filepath):
        return filepath
    
    # Final fallback: look for any tolkien_prompts files with timestamps
    pattern = os.path.join(static_dir, "tolkien_prompts*.txt")
    prompt_files = glob.glob(pattern)
    
    if not prompt_files:
        return None
    
    # Sort by modification time, most recent first
    prompt_files.sort(key=os.path.getmtime, reverse=True)
    return prompt_files[0]

def read_prompt_file(filepath: str) -> str:
    """
    Read and extract the visual prompts section from a prompt file
    
    Args:
        filepath: Path to the prompt file
        
    Returns:
        The visual prompts content
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Extract the section after "GENERATED VISUAL PROMPTS:"
        start_marker = "GENERATED VISUAL PROMPTS:"
        end_marker = "=" * 80  # The final separator
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            return content  # Fallback: return entire content
        
        start_idx = content.find("-" * 40, start_idx) + 40  # Skip the dashes
        end_idx = content.rfind(end_marker)
        
        if end_idx == -1:
            prompts_section = content[start_idx:].strip()
        else:
            prompts_section = content[start_idx:end_idx].strip()
        
        return prompts_section
        
    except Exception as e:
        raise Exception(f"Failed to read prompt file {filepath}: {e}")

# Example usage
async def main():
    """
    Example of how to use the image generator
    """
    # Load API key from environment or set directly
    load_dotenv()
    api_key = os.getenv("RUNWARE_API_KEY")
    
    if not api_key:
        print("Please set RUNWARE_API_KEY environment variable or update the code with your API key")
        return
    
    print("Starting image generation...")
    
    # Get the latest prompt file from static directory
    latest_prompt_file = get_latest_prompt_file("static")
    
    if latest_prompt_file:
        print(f"Found prompt file: {latest_prompt_file}")
        
        # Determine the output directory (same directory as the prompt file)
        output_dir = os.path.dirname(latest_prompt_file)
        
        try:
            # Read the prompts from the file
            scene_prompts = read_prompt_file(latest_prompt_file)
            
            # Generate images from the prompts in the same directory
            generated_paths = await generate_tolkien_scene_beats(
                scene_text=scene_prompts,
                api_key=api_key,
                base_output_dir=output_dir
            )
            print(f"Generated {len(generated_paths)} scene beat images")
            print(f"Images saved to: {output_dir}")
            
        except Exception as e:
            print(f"Error processing prompt file: {e}")
    else:
        print("No prompt files found in static/ directory.")
        print("Please run promptgen.py first to generate prompts.")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
