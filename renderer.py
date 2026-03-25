import base64
import math

from PIL import Image, ImageDraw, ImageFont

# Galactic Unicorn Leg display height
DISPLAY_HEIGHT = 11
# Max width for mono format
MAX_MONO_WIDTH = 5000
# Default font: PixelMplus10-Regular at 10px
DEFAULT_FONT_PATH = "fonts/PixelMplus10-Regular.ttf"
DEFAULT_FONT_SIZE = 10


def render_text_to_image(text, font_path=None, font_size=None):
    """Render text to an 11px-high 1-bit image."""
    font_path = font_path or DEFAULT_FONT_PATH
    font_size = font_size or DEFAULT_FONT_SIZE

    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError:
        font = ImageFont.load_default(size=font_size)

    # Measure text dimensions
    dummy = Image.new("1", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    width = min(max(text_width + 2, 1), MAX_MONO_WIDTH)
    img = Image.new("1", (width, DISPLAY_HEIGHT), color=0)
    draw = ImageDraw.Draw(img)

    # Center text in rows 1-10 (row 0 reserved for bar_color indicator)
    y_offset = max(0, (DISPLAY_HEIGHT - 1 - text_height) // 2) + 1 - bbox[1]
    draw.text((1, y_offset), text, fill=1, font=font)

    return img


def image_to_mono_bytes(img):
    """Convert PIL Image to mono format (1bit/pixel, MSB first, row-padded)."""
    width, height = img.size
    pixels = img.load()
    data = bytearray()

    for y in range(height):
        row_bytes = math.ceil(width / 8)
        for byte_idx in range(row_bytes):
            byte_val = 0
            for bit in range(8):
                x = byte_idx * 8 + bit
                if x < width and pixels[x, y]:
                    byte_val |= 1 << (7 - bit)
            data.append(byte_val)

    return bytes(data)


def render_text_to_bitmap_payload(text, color=None, bar_color=None,
                                  scroll_speed="medium", font_path=None, font_size=None):
    """Generate bitmap API payload from text.

    Uses mono format with optional bar_color for 1px indicator line at top.
    """
    color = color or {"r": 255, "g": 255, "b": 255}
    img = render_text_to_image(text, font_path=font_path, font_size=font_size)
    mono_data = image_to_mono_bytes(img)
    width = img.size[0]

    payload = {
        "width": width,
        "height": DISPLAY_HEIGHT,
        "format": "mono",
        "color": color,
        "display_mode": "scroll",
        "scroll_speed": scroll_speed,
        "data": base64.b64encode(mono_data).decode("ascii"),
    }

    if bar_color:
        payload["bar_color"] = bar_color

    return payload
