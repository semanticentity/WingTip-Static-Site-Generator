#!/usr/bin/env python3

# wingtip/generate_card.py
# Generate social card for GitHub Pages

import pathlib
import os
import re
import urllib.request
from PIL import Image, ImageDraw, ImageFont

def get_google_font(font_name):
    """Download and cache a Google Font"""
    # Convert font name to Google Fonts API format
    api_name = font_name.replace(' ', '+')
    
    # Create fonts cache directory
    cache_dir = pathlib.Path(__file__).parent / "fonts"
    cache_dir.mkdir(exist_ok=True)
    
    # Check if font is already cached
    font_file = cache_dir / f"{font_name.lower().replace(' ', '_')}.ttf"
    if font_file.exists():
        return str(font_file)
    
    try:
        # Get font CSS URL from Google Fonts API
        css_url = f"https://fonts.googleapis.com/css2?family={api_name}&display=swap"
        req = urllib.request.Request(css_url, headers={'User-Agent': 'Mozilla/5.0'})
        css = urllib.request.urlopen(req).read().decode('utf-8')
        
        # Extract TTF URL from CSS
        ttf_url = re.search(r'src: url\((.+?\.ttf)\)', css)
        if not ttf_url:
            return None
            
        # Download TTF file
        ttf_url = ttf_url.group(1)
        urllib.request.urlretrieve(ttf_url, font_file)
        return str(font_file)
    except Exception as e:
        print(f"Failed to download Google Font {font_name}: {e}")
        return None

def generate_social_card(title, tagline, theme="light", font="Poppins"):
    size = (1200, 630)
    bg_color = "#f6ede3"  # Warm background color
    fg_color = "#000000"  # Black text
    card = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(card)

    # Try to find or download the font
    try:
        # First try the specified font as a path
        font_path = font
        if not os.path.exists(font_path):
            # Then try bundled fonts directory
            font_path = os.path.join(os.path.dirname(__file__), "fonts", font)
        
        # If not found, try downloading from Google Fonts
        if not os.path.exists(font_path):
            google_font = get_google_font(font)
            if google_font:
                font_path = google_font
            else:
                # Fallback to Arial
                font_path = "Arial"

        title_font = ImageFont.truetype(font_path, 72)
        tagline_font = ImageFont.truetype(font_path, 40)
    except OSError:
        # If all else fails, use default bitmap font
        title_font = ImageFont.load_default()
        tagline_font = ImageFont.load_default()

    # Load and resize custom logo
    logo_width = 0  # Default if logo fails to load
    
    try:
        # Load the custom logo
        logo_path = "wingtip-logo.png"
        logo_img = Image.open(logo_path)
        
        # Convert to RGBA if needed
        if logo_img.mode != 'RGBA':
            logo_img = logo_img.convert('RGBA')
        
        # Make logo full height of card
        logo_height = size[1]  # Full height
        ratio = logo_img.width / logo_img.height
        logo_width = int(logo_height * ratio)
        logo_img = logo_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Position logo flush with left edge
        logo_y = 0  # Top edge
        logo_x = 0  # Left edge
        
        # Paste logo with alpha channel
        card.paste(logo_img, (logo_x, logo_y), logo_img)
    except Exception as e:
        print(f"Failed to load logo: {e}")
        # If logo fails, text will start from margin
    
    # Position text to the right of logo with spacing
    text_x = logo_width + 0  # 0px gap from logo
    text_y = size[1] // 3  # Start text 1/3 down from top
    
    # Draw title
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_height = title_bbox[3] - title_bbox[1]
    draw.text((text_x, text_y), title, font=title_font, fill=fg_color)
    
    # Draw tagline below title with 40px gap
    draw.text((text_x, text_y + title_height + 40), tagline, font=tagline_font, fill=fg_color)

    output = pathlib.Path("docs/site/social-card.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    card.save(output)
