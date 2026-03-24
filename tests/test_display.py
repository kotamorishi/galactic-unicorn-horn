from unittest import mock

from main import send_bitmap, clear_display, play_sound, COLOR_GREEN, COLOR_RED


class TestSendBitmap:
    def test_calls_bitmap_api(self):
        config = {"scroll_speed": "medium", "font_path": None, "font_size": 12}
        with mock.patch("main.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            send_bitmap("192.168.1.100", "Test", COLOR_GREEN, config)

        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "http://192.168.1.100/api/bitmap"

    def test_payload_has_bitmap_fields(self):
        config = {"scroll_speed": "medium", "font_path": None, "font_size": 12}
        with mock.patch("main.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            send_bitmap("192.168.1.100", "Hello", COLOR_RED, config)

        payload = mock_post.call_args[1]["json"]
        assert payload["format"] == "mono"
        assert payload["height"] == 11
        assert "width" in payload
        assert "data" in payload
        assert payload["color"] == COLOR_RED

    def test_custom_scroll_speed(self):
        config = {"scroll_speed": "fast", "font_path": None, "font_size": 12}
        with mock.patch("main.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            send_bitmap("10.0.0.1", "Test", COLOR_GREEN, config)

        payload = mock_post.call_args[1]["json"]
        assert payload["scroll_speed"] == "fast"

    def test_device_ip_in_url(self):
        config = {"scroll_speed": "medium", "font_path": None, "font_size": 12}
        with mock.patch("main.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            send_bitmap("10.0.0.50", "Test", COLOR_GREEN, config)

        url = mock_post.call_args[0][0]
        assert "10.0.0.50" in url


class TestClearDisplay:
    def test_calls_delete_bitmap(self):
        with mock.patch("main.requests.delete") as mock_delete:
            mock_delete.return_value.raise_for_status = mock.Mock()
            clear_display("192.168.1.100")

        mock_delete.assert_called_once()
        assert mock_delete.call_args[0][0] == "http://192.168.1.100/api/bitmap"


class TestPlaySound:
    def test_calls_sound_api(self):
        with mock.patch("main.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            play_sound("192.168.1.100", preset_id=4, volume=80)

        assert mock_post.call_args[0][0] == "http://192.168.1.100/api/sound/preview"
        payload = mock_post.call_args[1]["json"]
        assert payload["preset_id"] == 4
        assert payload["volume"] == 80

    def test_default_values(self):
        with mock.patch("main.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            play_sound("192.168.1.100")

        payload = mock_post.call_args[1]["json"]
        assert payload["preset_id"] == 1
        assert payload["volume"] == 75
