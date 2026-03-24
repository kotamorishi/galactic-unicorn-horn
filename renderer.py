import base64
import math

from PIL import Image, ImageDraw, ImageFont

# Galactic Unicorn Legのディスプレイ高さ
DISPLAY_HEIGHT = 11
# monoフォーマットの最大幅
MAX_MONO_WIDTH = 5000
# デフォルトフォント設定（PixelMplus12-Regular, 12px描画→11pxクロップ）
DEFAULT_FONT_PATH = "fonts/PixelMplus12-Regular.ttf"
DEFAULT_FONT_SIZE = 12


def render_text_to_image(text, font_path=None, font_size=None):
    """テキストを11px高の画像にレンダリングする

    12pxピクセルフォントで描画し、上1pxをクロップして11pxに収める。
    """
    font_path = font_path or DEFAULT_FONT_PATH
    font_size = font_size or DEFAULT_FONT_SIZE

    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError:
        font = ImageFont.load_default(size=font_size)

    # テキスト幅を計測
    dummy = Image.new("1", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]

    # 12px高で描画してから上1pxクロップで11pxにする
    render_height = font_size
    width = min(max(text_width + 2, 1), MAX_MONO_WIDTH)
    img = Image.new("1", (width, render_height), color=0)
    draw = ImageDraw.Draw(img)
    draw.text((1, -bbox[1]), text, fill=1, font=font)

    # 上1pxカットして11pxに
    crop_top = render_height - DISPLAY_HEIGHT
    if crop_top > 0:
        img = img.crop((0, crop_top, width, render_height))

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
