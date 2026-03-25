import os
from unittest import mock

from config import get_config


class TestGetConfig:
    def test_default_values(self):
        """環境変数未設定時のデフォルト値"""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = get_config()
        assert config["device_ip"] == "192.168.1.100"
        assert config["ical_urls"] == []
        assert config["fetch_interval"] == 300
        assert config["scroll_speed"] == "medium"
        assert config["font_path"] is None
        assert config["font_size"] == 10
        assert config["icloud_username"] is None
        assert config["icloud_app_password"] is None

    def test_icloud_credentials(self):
        """iCloud認証情報の読み込み"""
        env = {
            "ICLOUD_USERNAME": "user@icloud.com",
            "ICLOUD_APP_PASSWORD": "xxxx-xxxx-xxxx-xxxx",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = get_config()
        assert config["icloud_username"] == "user@icloud.com"
        assert config["icloud_app_password"] == "xxxx-xxxx-xxxx-xxxx"

    def test_icloud_empty_credentials(self):
        """iCloud認証情報が空の場合はNone"""
        env = {"ICLOUD_USERNAME": "", "ICLOUD_APP_PASSWORD": ""}
        with mock.patch.dict(os.environ, env, clear=True):
            config = get_config()
        assert config["icloud_username"] is None
        assert config["icloud_app_password"] is None

    def test_single_ical_url(self):
        """iCal URLが1つの場合"""
        env = {"ICAL_URLS": "https://example.com/cal.ics"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = get_config()
        assert config["ical_urls"] == ["https://example.com/cal.ics"]

    def test_multiple_ical_urls(self):
        """カンマ区切りで複数URLを指定"""
        env = {"ICAL_URLS": "https://a.com/1.ics, https://b.com/2.ics"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = get_config()
        assert config["ical_urls"] == ["https://a.com/1.ics", "https://b.com/2.ics"]

    def test_empty_urls_ignored(self):
        """空文字列やスペースのみのURLは無視される"""
        env = {"ICAL_URLS": "https://a.com/1.ics, , ,"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = get_config()
        assert config["ical_urls"] == ["https://a.com/1.ics"]

    def test_custom_device_ip(self):
        env = {"DEVICE_IP": "10.0.0.50"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = get_config()
        assert config["device_ip"] == "10.0.0.50"

    def test_custom_fetch_interval(self):
        env = {"FETCH_INTERVAL": "60"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = get_config()
        assert config["fetch_interval"] == 60

    def test_font_path_set(self):
        env = {"FONT_PATH": "/usr/share/fonts/noto.ttc"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = get_config()
        assert config["font_path"] == "/usr/share/fonts/noto.ttc"

    def test_font_size_custom(self):
        env = {"FONT_SIZE": "9"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = get_config()
        assert config["font_size"] == 9
