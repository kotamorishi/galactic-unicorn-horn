from unittest import mock

from main import send_to_display


class TestSendToDisplay:
    def test_calls_bitmap_api(self):
        """POST /api/bitmap が呼ばれる"""
        config = {"scroll_speed": "medium", "font_path": None, "font_size": 11}
        with mock.patch("main.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            send_to_display("192.168.1.100", "テスト", config)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://192.168.1.100/api/bitmap"

    def test_payload_has_bitmap_fields(self):
        """ペイロードにビットマップモード必須フィールドが含まれる"""
        config = {"scroll_speed": "medium", "font_path": None, "font_size": 11}
        with mock.patch("main.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            send_to_display("192.168.1.100", "Hello", config)

        payload = mock_post.call_args[1]["json"]
        assert payload["format"] == "mono"
        assert payload["height"] == 11
        assert "width" in payload
        assert "data" in payload
        assert payload["display_mode"] == "scroll"

    def test_custom_scroll_speed(self):
        """設定のscroll_speedが反映される"""
        config = {"scroll_speed": "fast", "font_path": None, "font_size": 11}
        with mock.patch("main.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            send_to_display("10.0.0.1", "Test", config)

        payload = mock_post.call_args[1]["json"]
        assert payload["scroll_speed"] == "fast"

    def test_device_ip_in_url(self):
        """指定したデバイスIPがURLに含まれる"""
        config = {"scroll_speed": "medium", "font_path": None, "font_size": 11}
        with mock.patch("main.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            send_to_display("10.0.0.50", "Test", config)

        url = mock_post.call_args[0][0]
        assert "10.0.0.50" in url
