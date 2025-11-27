from PIL import Image, ImageDraw
import os

def generate_settings_handle():
    width = 20
    height = 30
    
    # Colors (Matching settings_bg.py)
    bg_color = (60, 60, 75)       # Slightly lighter than bg
    border_light = (100, 100, 120)
    border_dark = (20, 20, 30)
    accent_color = (100, 150, 255)
    
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Main body
    draw.rectangle([1, 1, width-2, height-2], fill=bg_color)
    
    # Bevel borders
    # Top and Left (Light)
    draw.rectangle([0, 0, width-1, 1], fill=border_light) # Top
    draw.rectangle([0, 0, 1, height-1], fill=border_light) # Left
    
    # Bottom and Right (Dark)
    draw.rectangle([0, height-2, width-1, height-1], fill=border_dark) # Bottom
    draw.rectangle([width-2, 0, width-1, height-1], fill=border_dark) # Right
    
    # Grip lines (horizontal lines in the middle)
    center_x = width // 2
    center_y = height // 2
    
    line_color = (30, 30, 40)
    line_highlight = (90, 90, 110)
    
    for offset in [-4, 0, 4]:
        y = center_y + offset
        # Highlight below
        draw.line([4, y+1, width-5, y+1], fill=line_highlight, width=1)
        # Dark line
        draw.line([4, y, width-5, y], fill=line_color, width=1)

    # Save
    output_dir = os.path.join('assets', 'UI')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'settings_handle.png')
    img.save(output_path)
    print(f"Generated {output_path}")

if __name__ == "__main__":
    generate_settings_handle()
