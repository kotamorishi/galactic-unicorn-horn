from datetime import datetime, date, timedelta
from unittest import mock

from icloud_calendar import fetch_icloud_events, _parse_caldav_event


def _make_mock_vevent(summary, dtstart, dtend=None):
    """Create a mock CalDAV event."""
    vevent = mock.Mock()
    vevent.summary.value = summary
    vevent.dtstart.value = dtstart

    if dtend is not None:
        vevent.dtend.value = dtend
        # hasattr will return True for dtend
    else:
        # Make hasattr return False for dtend
        del vevent.dtend

    type(vevent).summary = mock.PropertyMock(return_value=mock.Mock(value=summary))

    event = mock.Mock()
    event.vobject_instance.vevent = vevent
    return event


def _make_mock_vevent_no_summary(dtstart):
    """Create a mock CalDAV event without summary."""
    vevent = mock.Mock(spec=[])
    vevent.dtstart = mock.Mock()
    vevent.dtstart.value = dtstart

    event = mock.Mock()
    event.vobject_instance.vevent = vevent
    return event


class TestParseCalDavEvent:
    def test_datetime_event(self):
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, 14, 0)
        event = _make_mock_vevent("Meeting", dt)
        result = _parse_caldav_event(event)
        assert result is not None
        assert result["summary"] == "Meeting"
        assert result["start"] == dt

    def test_event_with_end_time(self):
        now = datetime.now()
        start = datetime(now.year, now.month, now.day, 9, 0)
        end = datetime(now.year, now.month, now.day, 10, 0)
        event = _make_mock_vevent("ABC", start, end)
        result = _parse_caldav_event(event)
        assert result is not None
        assert result["end"] == end

    def test_event_without_end_time(self):
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, 14, 0)
        event = _make_mock_vevent("No end", dt)
        result = _parse_caldav_event(event)
        assert result is not None
        assert result["end"] is None

    def test_date_event(self):
        today = date.today()
        event = _make_mock_vevent("Holiday", today)
        result = _parse_caldav_event(event)
        assert result is not None
        assert result["summary"] == "Holiday"
        assert result["start"].date() == today

    def test_past_event_excluded(self):
        yesterday = datetime.now() - timedelta(days=2)
        dt = datetime(yesterday.year, yesterday.month, yesterday.day, 10, 0)
        event = _make_mock_vevent("Past", dt)
        result = _parse_caldav_event(event)
        assert result is None

    def test_future_event_excluded(self):
        future = datetime.now() + timedelta(days=3)
        dt = datetime(future.year, future.month, future.day, 10, 0)
        event = _make_mock_vevent("Future", dt)
        result = _parse_caldav_event(event)
        assert result is None

    def test_tomorrow_event_included(self):
        tomorrow = datetime.now() + timedelta(days=1)
        dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0)
        event = _make_mock_vevent("Tomorrow", dt)
        result = _parse_caldav_event(event)
        assert result is not None

    def test_no_summary(self):
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, 14, 0)
        event = _make_mock_vevent_no_summary(dt)
        result = _parse_caldav_event(event)
        assert result is not None
        assert result["summary"] == ""

    def test_timezone_aware_datetime(self):
        from datetime import timezone
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, 14, 0, tzinfo=timezone.utc)
        event = _make_mock_vevent("UTC", dt)
        result = _parse_caldav_event(event)
        assert result is not None
        assert result["start"].tzinfo is None


class TestFetchIcloudEvents:
    def test_fetches_from_all_calendars(self):
        now = datetime.now()
        ev1 = _make_mock_vevent("Work", datetime(now.year, now.month, now.day, 10, 0))
        ev2 = _make_mock_vevent("Personal", datetime(now.year, now.month, now.day, 15, 0))

        mock_cal1 = mock.Mock()
        mock_cal1.name = "Work"
        mock_cal1.search.return_value = [ev1]

        mock_cal2 = mock.Mock()
        mock_cal2.name = "Personal"
        mock_cal2.search.return_value = [ev2]

        with mock.patch("icloud_calendar.caldav.DAVClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.principal.return_value.calendars.return_value = [mock_cal1, mock_cal2]
            events = fetch_icloud_events("user@icloud.com", "xxxx-xxxx")

        assert len(events) == 2
        assert events[0]["summary"] == "Work"
        assert events[1]["summary"] == "Personal"

    def test_one_calendar_fails_gracefully(self):
        now = datetime.now()
        ev = _make_mock_vevent("OK", datetime(now.year, now.month, now.day, 10, 0))

        mock_cal1 = mock.Mock()
        mock_cal1.name = "Broken"
        mock_cal1.search.side_effect = Exception("Error")

        mock_cal2 = mock.Mock()
        mock_cal2.name = "Good"
        mock_cal2.search.return_value = [ev]

        with mock.patch("icloud_calendar.caldav.DAVClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.principal.return_value.calendars.return_value = [mock_cal1, mock_cal2]
            events = fetch_icloud_events("user@icloud.com", "xxxx-xxxx")

        assert len(events) == 1
        assert events[0]["summary"] == "OK"

    def test_empty_calendars(self):
        mock_cal = mock.Mock()
        mock_cal.name = "Empty"
        mock_cal.search.return_value = []

        with mock.patch("icloud_calendar.caldav.DAVClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.principal.return_value.calendars.return_value = [mock_cal]
            events = fetch_icloud_events("user@icloud.com", "xxxx-xxxx")

        assert events == []

    def test_events_sorted_by_start_time(self):
        now = datetime.now()
        ev1 = _make_mock_vevent("PM", datetime(now.year, now.month, now.day, 16, 0))
        ev2 = _make_mock_vevent("AM", datetime(now.year, now.month, now.day, 9, 0))

        mock_cal = mock.Mock()
        mock_cal.name = "Test"
        mock_cal.search.return_value = [ev1, ev2]

        with mock.patch("icloud_calendar.caldav.DAVClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.principal.return_value.calendars.return_value = [mock_cal]
            events = fetch_icloud_events("user@icloud.com", "xxxx-xxxx")

        assert events[0]["summary"] == "AM"
        assert events[1]["summary"] == "PM"
