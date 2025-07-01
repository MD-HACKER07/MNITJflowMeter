#!/usr/bin/env python3
"""
Create a simple icon for CICFlowMeter
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Create a simple application icon"""
    # Create a new image with transparent background
    size = (256, 256)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a blue circle
    circle_bbox = (20, 20, 236, 236)
    draw.ellipse(circle_bbox, fill=(0, 120, 215, 255), outline=(255, 255, 255, 255), width=5)
    
    # Draw 'CFM' text in the center
    try:
        # Try to load a font (this will work if you have Arial installed)
        font = ImageFont.truetype("arial.ttf", 100)
    except IOError:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Calculate text position (centered)
    text = "CFM"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2 - 20)
    
    # Draw text
    draw.text(position, text, fill=(255, 255, 255, 255), font=font)
    
    # Save as ICO file
    img.save('icon.ico', sizes=[(256, 256)])
    print("Icon created: icon.ico")

if __name__ == "__main__":
    create_icon()
