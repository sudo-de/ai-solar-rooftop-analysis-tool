from PIL import Image, ImageDraw
import os

def generate_sample_rooftop_image(output_path="samples/sample_rooftop_1.png"):
    """Generate a placeholder rooftop image."""
    # Create directories
    os.makedirs("samples", exist_ok=True)
    
    # Create 1920x1080 image
    width, height = 1920, 1080
    image = Image.new("RGB", (width, height), color=(100, 100, 100))  # Gray background
    draw = ImageDraw.Draw(image)
    
    # Draw rooftop (rectangle)
    draw.rectangle(
        [(200, 200), (1700, 880)], 
        fill=(150, 150, 150),  # Light gray rooftop
        outline=(0, 0, 0), 
        width=5
    )
    
    # Add mock obstructions (trees)
    draw.ellipse((300, 300, 400, 400), fill=(0, 100, 0)) # Tree 1
    draw.ellipse((1400, 600, 1500, 700), fill=(0, 100, 0))  # Tree 2
    
    # Save image
    image.save(output_path, "PNG")
    print(f"Generated sample image: {output_path}")

if __name__ == "__main__":
    generate_sample_rooftop_image()