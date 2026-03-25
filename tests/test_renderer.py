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
        img = render_text_to_image("Hello")
        assert img.size[1] == DISPLAY_HEIGHT

    def test_image_mode_is_1bit(self):
        img = render_text_to_image("Test")
        assert img.mode == "1"

    def test_nonempty_text_has_width(self):
        img = render_text_to_image("ABC")
        assert img.size[0] >= 1

    def test_longer_text_wider_image(self):
        img_short = render_text_to_image("A")
        img_long = render_text_to_image("ABCDEFGHIJKLMNOP")
        assert img_long.size[0] > img_short.size[0]

    def test_width_capped_at_max(self):
        img = render_text_to_image("X" * 10000)
        assert img.size[0] <= MAX_MONO_WIDTH

    def test_empty_text(self):
        img = render_text_to_image("")
        assert img.size[1] == DISPLAY_HEIGHT
        assert img.size[0] >= 1

    def test_japanese_text(self):
        img = render_text_to_image("予定なし")
        assert img.size[1] == DISPLAY_HEIGHT
        assert img.size[0] >= 1


class TestImageToMonoBytes:
    def test_single_white_pixel(self):
        img = Image.new("1", (1, 1), color=1)
        data = image_to_mono_bytes(img)
        assert data == bytes([0x80])

    def test_single_black_pixel(self):
        img = Image.new("1", (1, 1), color=0)
        data = image_to_mono_bytes(img)
        assert data == bytes([0x00])

    def test_8_pixel_row(self):
        img = Image.new("1", (8, 1), color=0)
        pixels = img.load()
        pixels[0, 0] = 1
        pixels[7, 0] = 1
        data = image_to_mono_bytes(img)
        assert data == bytes([0b10000001])

    def test_9_pixel_row_pads_to_2_bytes(self):
        img = Image.new("1", (9, 1), color=0)
        pixels = img.load()
        pixels[8, 0] = 1
        data = image_to_mono_bytes(img)
        assert len(data) == 2
        assert data[0] == 0x00
        assert data[1] == 0b10000000

    def test_multi_row(self):
        img = Image.new("1", (8, 3), color=0)
        data = image_to_mono_bytes(img)
        assert len(data) == 3

    def test_data_length_formula(self):
        for width, height in [(10, 11), (53, 11), (100, 11), (1, 1)]:
            img = Image.new("1", (width, height), color=0)
            data = image_to_mono_bytes(img)
            expected_len = math.ceil(width / 8) * height
            assert len(data) == expected_len, f"Failed for {width}x{height}"


class TestRenderTextToBitmapPayload:
    def test_payload_structure(self):
        payload = render_text_to_bitmap_payload("Test")
        assert payload["format"] == "mono"
        assert payload["height"] == DISPLAY_HEIGHT
        assert "width" in payload
        assert "data" in payload
        assert "color" in payload

    def test_data_is_valid_base64(self):
        payload = render_text_to_bitmap_payload("Hello")
        decoded = base64.b64decode(payload["data"])
        expected_len = math.ceil(payload["width"] / 8) * payload["height"]
        assert len(decoded) == expected_len

    def test_bar_color_included_when_set(self):
        payload = render_text_to_bitmap_payload(
            "Test", bar_color={"r": 0, "g": 255, "b": 0}
        )
        assert payload["bar_color"] == {"r": 0, "g": 255, "b": 0}

    def test_bar_color_omitted_when_none(self):
        payload = render_text_to_bitmap_payload("Test")
        assert "bar_color" not in payload

    def test_custom_color(self):
        color = {"r": 255, "g": 0, "b": 0}
        payload = render_text_to_bitmap_payload("Test", color=color)
        assert payload["color"] == color

    def test_default_color_is_white(self):
        payload = render_text_to_bitmap_payload("Test")
        assert payload["color"] == {"r": 255, "g": 255, "b": 255}

    def test_custom_scroll_speed(self):
        payload = render_text_to_bitmap_payload("Test", scroll_speed="fast")
        assert payload["scroll_speed"] == "fast"

    def test_display_mode_scroll(self):
        payload = render_text_to_bitmap_payload("Test")
        assert payload["display_mode"] == "scroll"
