import os
from dotenv import load_dotenv

load_dotenv()


def get_config():
    ical_urls_raw = os.getenv("ICAL_URLS", "")
    ical_urls = [url.strip() for url in ical_urls_raw.split(",") if url.strip()]

    font_path = os.getenv("FONT_PATH", "")
    icloud_username = os.getenv("ICLOUD_USERNAME", "")
    icloud_password = os.getenv("ICLOUD_APP_PASSWORD", "")

    return {
        "device_ip": os.getenv("DEVICE_IP", "192.168.1.100"),
        "ical_urls": ical_urls,
        "icloud_username": icloud_username if icloud_username else None,
        "icloud_app_password": icloud_password if icloud_password else None,
        "fetch_interval": int(os.getenv("FETCH_INTERVAL", "300")),
        "scroll_speed": os.getenv("SCROLL_SPEED", "medium"),
        "font_path": font_path if font_path else None,
        "font_size": int(os.getenv("FONT_SIZE", "12")),
    }
