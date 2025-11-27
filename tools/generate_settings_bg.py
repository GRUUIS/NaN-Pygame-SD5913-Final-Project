from PIL import Image, ImageDraw
import os

def generate_settings_bg():
    width = 400
    height = 200
    
    # Colors (Pixel art palette style)
    bg_color = (40, 40, 50)       # Dark grey-blue
    border_light = (80, 80, 100)  # Lighter highlight
    border_dark = (20, 20, 30)    # Darker shadow
    accent_color = (100, 150, 255) # Blue accent
    
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Main background rect (filled)
    draw.rectangle([2, 2, width-3, height-3], fill=bg_color)
    
    # Borders (Bevel effect)
    # Top and Left (Light)
    draw.rectangle([0, 0, width-1, 2], fill=border_light) # Top
    draw.rectangle([0, 0, 2, height-1], fill=border_light) # Left
    
    # Bottom and Right (Dark)
    draw.rectangle([0, height-3, width-1, height-1], fill=border_dark) # Bottom
    draw.rectangle([width-3, 0, width-1, height-1], fill=border_dark) # Right
    
    # Inner border (1px dark line inside)
    draw.rectangle([6, 6, width-7, height-7], outline=border_dark, width=2)
    
    # Corner accents (screws/bolts)
    corner_dist = 12
    bolt_size = 3
    corners = [
        (corner_dist, corner_dist),
        (width - corner_dist - 1, corner_dist),
        (corner_dist, height - corner_dist - 1),
        (width - corner_dist - 1, height - corner_dist - 1)
    ]
    
    for cx, cy in corners:
        # Bolt shadow
        draw.rectangle([cx-bolt_size+1, cy-bolt_size+1, cx+bolt_size+1, cy+bolt_size+1], fill=border_dark)
        # Bolt face
        draw.rectangle([cx-bolt_size, cy-bolt_size, cx+bolt_size, cy+bolt_size], fill=(120, 120, 130))
        # Bolt slot
        draw.line([cx-1, cy-1, cx+1, cy+1], fill=border_dark, width=1)

    # Decorative header bar
    draw.rectangle([10, 30, width-10, 32], fill=border_dark)
    
    # Save
    output_dir = os.path.join('assets', 'UI')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, 'settings_background.png')
    img.save(output_path)
    print(f"Generated settings background at {output_path}")

if __name__ == "__main__":
    generate_settings_bg()
