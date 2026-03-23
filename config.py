import os
from dotenv import load_dotenv

load_dotenv()


def get_config():
    ical_urls_raw = os.getenv("ICAL_URLS", "")
    ical_urls = [url.strip() for url in ical_urls_raw.split(",") if url.strip()]

    return {
        "device_ip": os.getenv("DEVICE_IP", "192.168.1.100"),
        "ical_urls": ical_urls,
        "fetch_interval": int(os.getenv("FETCH_INTERVAL", "300")),
        "scroll_speed": os.getenv("SCROLL_SPEED", "medium"),
        "font": os.getenv("FONT", "bitmap8"),
    }
