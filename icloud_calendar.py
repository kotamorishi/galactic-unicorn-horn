import logging
from datetime import datetime, timedelta, date

import caldav

logger = logging.getLogger(__name__)

ICLOUD_CALDAV_URL = "https://caldav.icloud.com/"


def fetch_icloud_events(username, app_password):
    """iCloud CalDAVからプライベートカレンダーのイベントを取得する

    今日と明日のイベントを全カレンダーから取得して返す。
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
            logger.info("%d件のイベントを取得: iCloud/%s", len(cal_events), cal.name)
        except Exception:
            logger.exception("iCloudカレンダー取得エラー: %s", cal.name)

    return sorted(all_events, key=lambda e: e["start"])


def _parse_caldav_event(event):
    """CalDAVイベントオブジェクトをパースする"""
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

        now = datetime.now()
        tomorrow_end = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
        if now.date() <= event_date.date() <= tomorrow_end.date():
            return {"start": event_date, "summary": summary}
    except Exception:
        logger.exception("イベントのパースに失敗")
    return None
