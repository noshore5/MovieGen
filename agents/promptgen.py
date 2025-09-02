import os
import random
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

def list_available_models():
    """
    List all available models to identify the correct one to use.
    """
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    models = genai.list_models()
    for model in models:
        print(f"Model ID: {model.name}, Description: {model.description}")

def get_random_quote(file_path):
    """
    Read a random quote from the given file.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        quotes = [line.strip() for line in file if line.strip()]
    return random.choice(quotes)


def generateprompts_tolkien(quote):
    """
    Given a Tolkien quote, generate 3-6 detailed AI image prompts
    including inferred characters, setting, mood, and style.
    """
    prompt = f"""
    You are a Tolkienverse visual story agent and expert in Middle-earth lore.
    Your task is to analyze the following quote and infer its specific scene:
    - Identify the characters involved (if any) or the type of observer implied.
    - Determine the setting, including location, time period, and environmental details.
    - Describe the mood and tone of the scene.
    - Highlight any important objects or elements that define the scene.

    Then, break the scene into 4-6 visual beats suitable for AI image generation:
    - At least 2 beats should focus on visualizing the subject of the quote.
    - The remaining beats can focus on the scene in which the quote is spoken (e.g., characters, setting, mood, or objects).
    - Use Tolkien-style fantasy cues, cinematic lighting, and high detail.
    - Ensure the prompts are vivid, descriptive, and immersive.

    Quote: "{quote}"

    Output the analysis and prompts in this EXACT format:

    ## Scene Context Inference
    [Your scene analysis here]

    ## Visual Beats

    **PROMPT_1:**
    [Detailed image prompt here - no quotes, just the raw prompt text]

    **PROMPT_2:**
    [Detailed image prompt here - no quotes, just the raw prompt text]

    **PROMPT_3:**
    [Detailed image prompt here - no quotes, just the raw prompt text]

    **PROMPT_4:**
    [Detailed image prompt here - no quotes, just the raw prompt text]

    Continue with PROMPT_5 and PROMPT_6 if you create more beats.
    """

    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("models/gemini-2.5-flash")  # Replace with a valid model ID
    response = model.generate_content(prompt)
    return response.text

def generateprompts(quote):
    """
    Given a quote, generate 4-6 detailed AI image prompts
    including inferred characters, setting, mood, and style.
    """
    prompt = f"""
    You are a visual story agent.
    Your task is to analyze the following quote and infer its specific scene:
    - Identify the characters involved (if any) or the type of observer implied.
    - Determine the setting, including location, time period, and environmental details.
    - Describe the mood and tone of the scene.
    - Highlight any important objects or elements that define the scene.

    Then, break the scene into 5-7 visual beats suitable for AI image generation:
    - At least 2 beats should focus on visualizing the subject of the quote.
    - The remaining beats can focus on the scene in which the quote is spoken (e.g., characters, setting, mood, or objects).
    - Use environmental cues, cinematic lighting, and high detail.
    - Ensure the prompts are vivid, descriptive, and immersive.

    Quote: "{quote}"

    Output the analysis and prompts in this EXACT format:

    ## Scene Context Inference
    [Your scene analysis here]

    ## Visual Beats

    **PROMPT_1:**
    [Detailed image prompt here - no quotes, just the raw prompt text]

    **PROMPT_2:**
    [Detailed image prompt here - no quotes, just the raw prompt text]

    **PROMPT_3:**
    [Detailed image prompt here - no quotes, just the raw prompt text]

    **PROMPT_4:**
    [Detailed image prompt here - no quotes, just the raw prompt text]

    Continue with PROMPT_5 and beyond.
     """

    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("models/gemini-2.5-flash")  # Replace with a valid model ID
    response = model.generate_content(prompt)
    return response.text

def save_prompts_to_file(quote, prompts, output_dir="static"):
    """
    Save the quote and generated prompts to a text file in the specified directory.
    
    Args:
        quote: The original Tolkien quote
        prompts: The generated visual prompts
        output_dir: Directory to save the file (default: "static")
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename without timestamp
    filename = f"tolkien_prompts.txt"
    filepath = os.path.join(output_dir, filename)
    
    # Write content to file
    with open(filepath, "w", encoding="utf-8") as file:
        file.write("=" * 80 + "\n")
        file.write("TOLKIEN QUOTE AND VISUAL PROMPTS\n")
        file.write("=" * 80 + "\n\n")
        
        file.write("ORIGINAL QUOTE:\n")
        file.write("-" * 40 + "\n")
        file.write(f'"{quote}"\n\n')
        
        file.write("GENERATED VISUAL PROMPTS:\n")
        file.write("-" * 40 + "\n")
        file.write(prompts)
        file.write("\n\n")
        
        file.write("=" * 80 + "\n")
        file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write("=" * 80 + "\n")
    
    return filepath