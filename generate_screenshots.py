from PIL import Image, ImageDraw, ImageFont
import os

def generate_placeholder_screenshot(filename, text):
    """Generate a placeholder screenshot."""
    os.makedirs("screenshots", exist_ok=True)
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    draw.rectangle([(50, 50), (1230, 670)], fill=(200, 200, 200))
    draw.text((100, 100), text, fill=(0, 0, 0), font=font)
    
    output_path = os.path.join("screenshots", filename)
    image.save(output_path, "PNG")
    print(f"Generated placeholder: {output_path}")

if __name__ == "__main__":
    generate_placeholder_screenshot("streamlit_ui.png", "Streamlit UI Placeholder")
    generate_placeholder_screenshot("results_display.png", "Results Display Placeholder")