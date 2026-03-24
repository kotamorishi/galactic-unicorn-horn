import logging
from datetime import datetime, timedelta, date

import caldav

logger = logging.getLogger(__name__)

ICLOUD_CALDAV_URL = "https://caldav.icloud.com/"


def fetch_icloud_events(username, app_password):
    """Fetch private calendar events from iCloud via CalDAV.

    Returns today's and tomorrow's events from all calendars.
    """
    client = caldav.DAVClient(
        url=ICLOUD_CALDAV_URL,
        username=username,
        password=app_password,
    )
    principal = client.principal()
    calendars = principal.calendars()

    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = (start + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)

    all_events = []
    for cal in calendars:
        try:
            cal_events = cal.search(start=start, end=end, event=True, expand=True)
            for event in cal_events:
                parsed = _parse_caldav_event(event)
                if parsed:
                    all_events.append(parsed)
            logger.info("Fetched %d events: iCloud/%s", len(cal_events), cal.name)
        except Exception:
            logger.exception("Failed to fetch iCloud calendar: %s", cal.name)

    return sorted(all_events, key=lambda e: e["start"])


def _parse_caldav_event(event):
    """Parse a CalDAV event object into a dict."""
    try:
        vevent = event.vobject_instance.vevent
        summary = str(vevent.summary.value) if hasattr(vevent, "summary") else ""
        dtstart = vevent.dtstart.value

        if isinstance(dtstart, datetime):
            event_date = dtstart.replace(tzinfo=None)
        elif isinstance(dtstart, date):
            event_date = datetime.combine(dtstart, datetime.min.time())
        else:
            return None

        # Parse end time
        end_date = None
        if hasattr(vevent, "dtend"):
            dtend = vevent.dtend.value
            if isinstance(dtend, datetime):
                end_date = dtend.replace(tzinfo=None)
            elif isinstance(dtend, date):
                end_date = datetime.combine(dtend, datetime.min.time())

        now = datetime.now()
        tomorrow_end = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
        if now.date() <= event_date.date() <= tomorrow_end.date():
            return {"start": event_date, "end": end_date, "summary": summary}
    except Exception:
        logger.exception("Failed to parse event")
    return None
