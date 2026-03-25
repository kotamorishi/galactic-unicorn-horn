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

# Display timing constants
NOTIFY_BEFORE_MINUTES = 10  # Show notification before event start
DISPLAY_AFTER_START_MINUTES = 5  # Keep showing after event starts

# Colors
COLOR_WHITE = {"r": 255, "g": 255, "b": 255}
COLOR_GREEN = {"r": 0, "g": 255, "b": 0}
COLOR_RED = {"r": 255, "g": 0, "b": 0}


def fetch_events(ical_url):
    """Fetch events from an iCal URL for today and tomorrow."""
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

        if isinstance(dt, datetime):
            event_date = dt.replace(tzinfo=None)
        else:
            event_date = datetime.combine(dt, datetime.min.time())

        if now.date() <= event_date.date() <= tomorrow_end.date():
            summary = str(component.get("summary", ""))
            # Parse end time
            dtend = component.get("dtend")
            end_date = None
            if dtend:
                end_dt = dtend.dt
                if isinstance(end_dt, datetime):
                    end_date = end_dt.replace(tzinfo=None)
                else:
                    end_date = datetime.combine(end_dt, datetime.min.time())

            events.append({
                "start": event_date,
                "end": end_date,
                "summary": summary,
            })

    return sorted(events, key=lambda e: e["start"])


def fetch_all_events(ical_urls):
    """Fetch and merge events from multiple iCal URLs."""
    all_events = []
    for url in ical_urls:
        try:
            events = fetch_events(url)
            all_events.extend(events)
            logger.info("Fetched %d events: %s", len(events), url[:50])
        except Exception:
            logger.exception("Failed to fetch calendar: %s", url[:50])
    return sorted(all_events, key=lambda e: e["start"])


def fetch_all_calendar_events(config):
    """Fetch events from all sources (iCal URLs + iCloud CalDAV)."""
    all_events = []

    if config["ical_urls"]:
        all_events.extend(fetch_all_events(config["ical_urls"]))

    if config["icloud_username"] and config["icloud_app_password"]:
        try:
            icloud_events = fetch_icloud_events(
                config["icloud_username"],
                config["icloud_app_password"],
            )
            all_events.extend(icloud_events)
            logger.info("iCloud: fetched %d events", len(icloud_events))
        except Exception:
            logger.exception("Failed to fetch iCloud calendar")

    return sorted(all_events, key=lambda e: e["start"])


def format_event_text(event):
    """Format a single event for LED display (e.g. '09:00-10:00 ABC')."""
    start_str = event["start"].strftime("%H:%M")
    if event.get("end"):
        end_str = event["end"].strftime("%H:%M")
        return f"{start_str}-{end_str} {event['summary']}"
    return f"{start_str} {event['summary']}"


def get_event_phase(event, now):
    """Determine the display phase for an event.

    Returns:
        "notify"  — 10 min before start until start (green + sound)
        "active"  — start until 5 min after start (red)
        "off"     — outside display window
    """
    start = event["start"]
    notify_time = start - timedelta(minutes=NOTIFY_BEFORE_MINUTES)
    display_end = start + timedelta(minutes=DISPLAY_AFTER_START_MINUTES)

    if notify_time <= now < start:
        return "notify"
    elif start <= now < display_end:
        return "active"
    else:
        return "off"


def check_device(device_ip):
    """Check if the LED device is reachable via GET /api/status."""
    try:
        url = f"http://{device_ip}/api/status"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Device online - time: %s %s", data.get("day", ""), data.get("time", ""))
        return True
    except Exception:
        logger.warning("Device unreachable at %s", device_ip)
        return False


def send_bitmap(device_ip, text, indicator_color, config):
    """Send bitmap text to LED display with 1px color indicator line."""
    payload = render_text_to_bitmap_payload(
        text,
        color=COLOR_WHITE,
        bar_color=indicator_color,
        scroll_speed=config["scroll_speed"],
        font_path=config.get("font_path"),
        font_size=config.get("font_size", 10),
    )
    url = f"http://{device_ip}/api/bitmap"
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    logger.info("Display updated: %s", text[:50])


def clear_display(device_ip):
    """Clear bitmap display."""
    url = f"http://{device_ip}/api/bitmap"
    resp = requests.delete(url, timeout=10)
    resp.raise_for_status()
    logger.info("Display cleared")


def play_sound(device_ip, preset_id=1, volume=75):
    """Play a notification sound on the device."""
    url = f"http://{device_ip}/api/sound/preview"
    payload = {"preset_id": preset_id, "volume": volume}
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    logger.info("Sound played: preset=%d, volume=%d", preset_id, volume)


def main():
    config = get_config()

    has_ical = bool(config["ical_urls"])
    has_icloud = bool(config["icloud_username"] and config["icloud_app_password"])

    if not has_ical and not has_icloud:
        logger.error("No calendar configured. Check your .env file.")
        return

    sources = []
    if has_ical:
        sources.append(f"iCal URL x{len(config['ical_urls'])}")
    if has_icloud:
        sources.append("iCloud CalDAV")
    device_ips = config["device_ips"]
    logger.info("Starting - devices: %s, sources: %s", ", ".join(device_ips), ", ".join(sources))
    logger.info("Fetch interval: %ds", config["fetch_interval"])

    events = []
    last_fetch = None
    notified_events_10min = set()  # Track events where 10-min sound has been played
    notified_events_5min = set()  # Track events where 5-min sound has been played
    current_display = None  # Track what's currently displayed

    available_devices = set()

    while True:
        try:
            now = datetime.now()

            # Fetch events periodically
            if last_fetch is None or (now - last_fetch).total_seconds() >= config["fetch_interval"]:
                events = fetch_all_calendar_events(config)
                last_fetch = now
                logger.info("Fetched %d events total", len(events))
                # Check device connectivity at each fetch cycle
                available_devices = {ip for ip in device_ips if check_device(ip)}

            if not available_devices:
                time.sleep(10)
                continue

            # Find the highest priority event to display
            display_event = None
            display_phase = None

            for event in events:
                phase = get_event_phase(event, now)
                if phase == "active":
                    # Active events take highest priority
                    display_event = event
                    display_phase = phase
                    break
                elif phase == "notify" and display_phase != "active":
                    # Notify phase, but only if no active event
                    display_event = event
                    display_phase = phase

            # Update display based on current state
            if display_event and display_phase == "notify":
                event_key = (display_event["start"], display_event["summary"])
                text = format_event_text(display_event)

                # Play sound at 10 min before
                if event_key not in notified_events_10min:
                    for ip in available_devices:
                        try:
                            play_sound(ip, preset_id=5, volume=70)
                        except Exception:
                            logger.exception("Failed to play sound on %s", ip)
                    notified_events_10min.add(event_key)
                    time.sleep(1)  # Wait before sending bitmap

                # Play sound again at 5 min before
                five_min_before = display_event["start"] - timedelta(minutes=5)
                if now >= five_min_before and event_key not in notified_events_5min:
                    for ip in available_devices:
                        try:
                            play_sound(ip, preset_id=5, volume=70)
                        except Exception:
                            logger.exception("Failed to play sound on %s", ip)
                    notified_events_5min.add(event_key)
                    time.sleep(1)

                if current_display != ("notify", event_key):
                    for ip in available_devices:
                        send_bitmap(ip, text, COLOR_GREEN, config)
                    current_display = ("notify", event_key)

            elif display_event and display_phase == "active":
                event_key = (display_event["start"], display_event["summary"])
                text = format_event_text(display_event)

                if current_display != ("active", event_key):
                    for ip in available_devices:
                        send_bitmap(ip, text, COLOR_RED, config)
                    current_display = ("active", event_key)

            else:
                # No event to display — clear if something was showing
                if current_display is not None:
                    for ip in available_devices:
                        try:
                            clear_display(ip)
                        except Exception:
                            logger.exception("Failed to clear display on %s", ip)
                    current_display = None

            # Clean up old notified events
            cutoff = now - timedelta(minutes=DISPLAY_AFTER_START_MINUTES)
            notified_events_10min = {
                key for key in notified_events_10min
                if key[0] > cutoff
            }
            notified_events_5min = {
                key for key in notified_events_5min
                if key[0] > cutoff
            }

        except Exception:
            logger.exception("Error in main loop")

        time.sleep(10)  # Check every 10 seconds


if __name__ == "__main__":
    main()
