import base64
import math

from PIL import Image

from renderer import (
    DISPLAY_HEIGHT,
    MAX_MONO_WIDTH,
    image_to_mono_bytes,
    render_text_to_bitmap_payload,
    render_text_to_image,
)


class TestRenderTextToImage:
    def test_image_height_is_11(self):
        """画像の高さは常に11px"""
        img = render_text_to_image("Hello")
        assert img.size[1] == DISPLAY_HEIGHT

    def test_image_mode_is_1bit(self):
        """画像は1bitモノクロ"""
        img = render_text_to_image("Test")
        assert img.mode == "1"

    def test_nonempty_text_has_width(self):
        """テキストがあれば幅が1以上"""
        img = render_text_to_image("ABC")
        assert img.size[0] >= 1

    def test_longer_text_wider_image(self):
        """長いテキストは幅が大きくなる"""
        img_short = render_text_to_image("A")
        img_long = render_text_to_image("ABCDEFGHIJKLMNOP")
        assert img_long.size[0] > img_short.size[0]

    def test_width_capped_at_max(self):
        """幅はMAX_MONO_WIDTHを超えない"""
        img = render_text_to_image("X" * 10000)
        assert img.size[0] <= MAX_MONO_WIDTH

    def test_empty_text(self):
        """空文字列でもエラーにならない"""
        img = render_text_to_image("")
        assert img.size[1] == DISPLAY_HEIGHT
        assert img.size[0] >= 1

    def test_japanese_text(self):
        """日本語テキストでもエラーにならない"""
        img = render_text_to_image("予定なし")
        assert img.size[1] == DISPLAY_HEIGHT
        assert img.size[0] >= 1


class TestImageToMonoBytes:
    def test_single_white_pixel(self):
        """1x1 白(1)ピクセル → 0b10000000 = 0x80"""
        img = Image.new("1", (1, 1), color=1)
        data = image_to_mono_bytes(img)
        assert data == bytes([0x80])

    def test_single_black_pixel(self):
        """1x1 黒(0)ピクセル → 0x00"""
        img = Image.new("1", (1, 1), color=0)
        data = image_to_mono_bytes(img)
        assert data == bytes([0x00])

    def test_8_pixel_row(self):
        """8px幅 → ちょうど1バイト/行、パディングなし"""
        img = Image.new("1", (8, 1), color=0)
        pixels = img.load()
        pixels[0, 0] = 1  # MSB
        pixels[7, 0] = 1  # LSB
        data = image_to_mono_bytes(img)
        assert data == bytes([0b10000001])

    def test_9_pixel_row_pads_to_2_bytes(self):
        """9px幅 → 2バイト/行（7bitパディング）"""
        img = Image.new("1", (9, 1), color=0)
        pixels = img.load()
        pixels[8, 0] = 1  # 9番目のピクセル
        data = image_to_mono_bytes(img)
        assert len(data) == 2
        assert data[0] == 0x00
        assert data[1] == 0b10000000

    def test_multi_row(self):
        """複数行の場合、行数分のバイト列になる"""
        img = Image.new("1", (8, 3), color=0)
        data = image_to_mono_bytes(img)
        # 8px幅 = 1バイト/行 × 3行 = 3バイト
        assert len(data) == 3

    def test_data_length_formula(self):
        """データ長 = ceil(width/8) * height"""
        for width, height in [(10, 11), (53, 11), (100, 11), (1, 1)]:
            img = Image.new("1", (width, height), color=0)
            data = image_to_mono_bytes(img)
            expected_len = math.ceil(width / 8) * height
            assert len(data) == expected_len, f"Failed for {width}x{height}"


class TestRenderTextToBitmapPayload:
    def test_payload_structure(self):
        """ペイロードに必要なキーが全て含まれる"""
        payload = render_text_to_bitmap_payload("Test")
        assert "width" in payload
        assert "height" in payload
        assert payload["height"] == DISPLAY_HEIGHT
        assert payload["format"] == "mono"
        assert "color" in payload
        assert "display_mode" in payload
        assert "scroll_speed" in payload
        assert "data" in payload

    def test_data_is_valid_base64(self):
        """dataフィールドがbase64デコード可能"""
        payload = render_text_to_bitmap_payload("Hello")
        decoded = base64.b64decode(payload["data"])
        expected_len = math.ceil(payload["width"] / 8) * payload["height"]
        assert len(decoded) == expected_len

    def test_custom_color(self):
        """カスタムカラーを指定可能"""
        color = {"r": 255, "g": 0, "b": 0}
        payload = render_text_to_bitmap_payload("Test", color=color)
        assert payload["color"] == color

    def test_custom_scroll_speed(self):
        """スクロール速度を指定可能"""
        payload = render_text_to_bitmap_payload("Test", scroll_speed="fast")
        assert payload["scroll_speed"] == "fast"

    def test_default_color(self):
        """デフォルトカラーが設定される"""
        payload = render_text_to_bitmap_payload("Test")
        assert payload["color"] == {"r": 0, "g": 255, "b": 128}

    def test_display_mode_scroll(self):
        payload = render_text_to_bitmap_payload("Test")
        assert payload["display_mode"] == "scroll"
