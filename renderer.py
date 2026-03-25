import base64
import math

from PIL import Image, ImageDraw, ImageFont

# Galactic Unicorn Legのディスプレイ高さ
DISPLAY_HEIGHT = 11
# monoフォーマットの最大幅
MAX_MONO_WIDTH = 5000
# Default font: PixelMplus10-Regular at 10px, centered in 11px display
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

    # Vertically center the text
    y_offset = max(0, (DISPLAY_HEIGHT - text_height) // 2) - bbox[1]
    draw.text((1, y_offset), text, fill=1, font=font)

    return img


def image_to_mono_bytes(img):
    """PIL Imageをmonoフォーマット（1bit/pixel, MSB first, 行ごとにバイト境界パディング）に変換"""
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


def render_text_to_bitmap_payload(text, color=None, scroll_speed="medium", font_path=None, font_size=None):
    """テキストからビットマップAPI用のペイロードを生成する"""
    img = render_text_to_image(text, font_path=font_path, font_size=font_size)
    mono_data = image_to_mono_bytes(img)
    width, height = img.size

    return {
        "width": width,
        "height": height,
        "format": "mono",
        "color": color or {"r": 0, "g": 255, "b": 128},
        "display_mode": "scroll",
        "scroll_speed": scroll_speed,
        "data": base64.b64encode(mono_data).decode("ascii"),
    }
