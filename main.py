import time
import logging
from datetime import datetime, timedelta

import requests
from icalendar import Calendar

from config import get_config
from icloud_calendar import fetch_icloud_events
from renderer import render_text_to_bitmap_payload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_events(ical_url):
    """iCal URLからイベントを取得し、今日と明日のイベントを返す"""
    resp = requests.get(ical_url, timeout=30)
    resp.raise_for_status()
    cal = Calendar.from_ical(resp.text)

    now = datetime.now()
    tomorrow_end = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
    events = []

    for component in cal.walk("VEVENT"):
        dtstart = component.get("dtstart")
        if dtstart is None:
            continue
        dt = dtstart.dt

        # 終日イベントはdateオブジェクト、時刻付きはdatetimeオブジェクト
        if isinstance(dt, datetime):
            event_date = dt.replace(tzinfo=None)
        else:
            event_date = datetime.combine(dt, datetime.min.time())

        if now.date() <= event_date.date() <= tomorrow_end.date():
            summary = str(component.get("summary", ""))
            events.append({"start": event_date, "summary": summary})

    return sorted(events, key=lambda e: e["start"])


def fetch_all_events(ical_urls):
    """複数のiCal URLからイベントを取得して統合する"""
    all_events = []
    for url in ical_urls:
        try:
            events = fetch_events(url)
            all_events.extend(events)
            logger.info("%d件のイベントを取得: %s", len(events), url[:50])
        except Exception:
            logger.exception("カレンダー取得エラー: %s", url[:50])
    return sorted(all_events, key=lambda e: e["start"])


def format_events_text(events):
    """イベントリストを表示用テキストに変換する"""
    if not events:
        return "予定なし"

    now = datetime.now()
    lines = []
    for event in events:
        dt = event["start"]
        if dt.date() == now.date():
            time_str = dt.strftime("%H:%M")
        else:
            time_str = "明日 " + dt.strftime("%H:%M")

        # 終日イベント（00:00）は時刻を省略
        if dt.hour == 0 and dt.minute == 0:
            if dt.date() == now.date():
                time_str = "終日"
            else:
                time_str = "明日"

        lines.append(f"{time_str} {event['summary']}")

    return " | ".join(lines)


def send_to_display(device_ip, text, config):
    """ビットマップモードでテキストをLEDに送信する"""
    payload = render_text_to_bitmap_payload(
        text,
        color={"r": 0, "g": 255, "b": 128},
        scroll_speed=config["scroll_speed"],
        font_path=config.get("font_path"),
        font_size=config.get("font_size", 11),
    )
    url = f"http://{device_ip}/api/bitmap"
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    logger.info("ビットマップ表示更新: %s", text[:50])


def fetch_all_calendar_events(config):
    """全ソース（iCal URL + iCloud CalDAV）からイベントを取得して統合する"""
    all_events = []

    # iCal URL方式（Google カレンダー等）
    if config["ical_urls"]:
        all_events.extend(fetch_all_events(config["ical_urls"]))

    # iCloud CalDAV方式（Apple カレンダー）
    if config["icloud_username"] and config["icloud_app_password"]:
        try:
            icloud_events = fetch_icloud_events(
                config["icloud_username"],
                config["icloud_app_password"],
            )
            all_events.extend(icloud_events)
            logger.info("iCloud: %d件のイベントを取得", len(icloud_events))
        except Exception:
            logger.exception("iCloudカレンダー取得エラー")

    return sorted(all_events, key=lambda e: e["start"])


def main():
    config = get_config()

    has_ical = bool(config["ical_urls"])
    has_icloud = bool(config["icloud_username"] and config["icloud_app_password"])

    if not has_ical and not has_icloud:
        logger.error("カレンダーが設定されていません。.envファイルを確認してください。")
        return

    sources = []
    if has_ical:
        sources.append(f"iCal URL {len(config['ical_urls'])}件")
    if has_icloud:
        sources.append("iCloud CalDAV")
    logger.info("開始 - デバイス: %s, ソース: %s", config["device_ip"], ", ".join(sources))
    logger.info("取得間隔: %d秒", config["fetch_interval"])

    while True:
        try:
            events = fetch_all_calendar_events(config)
            text = format_events_text(events)
            send_to_display(config["device_ip"], text, config)
        except Exception:
            logger.exception("メインループでエラーが発生")

        time.sleep(config["fetch_interval"])


if __name__ == "__main__":
    main()
