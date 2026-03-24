import os
from dotenv import load_dotenv

load_dotenv()


def get_config():
    ical_urls_raw = os.getenv("ICAL_URLS", "")
    ical_urls = [url.strip() for url in ical_urls_raw.split(",") if url.strip()]

    font_path = os.getenv("FONT_PATH", "")

    return {
        "device_ip": os.getenv("DEVICE_IP", "192.168.1.100"),
        "ical_urls": ical_urls,
        "fetch_interval": int(os.getenv("FETCH_INTERVAL", "300")),
        "scroll_speed": os.getenv("SCROLL_SPEED", "medium"),
        "font_path": font_path if font_path else None,
        "font_size": int(os.getenv("FONT_SIZE", "12")),
    }
