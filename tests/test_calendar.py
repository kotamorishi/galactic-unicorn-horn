from datetime import datetime, date, timedelta
from unittest import mock

from icalendar import Calendar, Event

from main import fetch_events, fetch_all_events, format_event_text, get_event_phase


def _make_ical(events_data):
    """Generate iCal data for testing."""
    cal = Calendar()
    cal.add("prodid", "-//Test//Test//EN")
    cal.add("version", "2.0")
    for ev_data in events_data:
        event = Event()
        event.add("summary", ev_data["summary"])
        event.add("dtstart", ev_data["dtstart"])
        if "dtend" in ev_data:
            event.add("dtend", ev_data["dtend"])
        cal.add_component(event)
    return cal.to_ical().decode("utf-8")


class TestFetchEvents:
    def test_today_event_returned(self):
        now = datetime.now()
        today_event = datetime(now.year, now.month, now.day, 14, 0)
        ical_data = _make_ical([{"summary": "Meeting", "dtstart": today_event}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert len(events) == 1
        assert events[0]["summary"] == "Meeting"

    def test_event_has_end_time(self):
        now = datetime.now()
        start = datetime(now.year, now.month, now.day, 9, 0)
        end = datetime(now.year, now.month, now.day, 10, 0)
        ical_data = _make_ical([{"summary": "ABC", "dtstart": start, "dtend": end}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert events[0]["end"] == end

    def test_event_without_end_time(self):
        now = datetime.now()
        start = datetime(now.year, now.month, now.day, 9, 0)
        ical_data = _make_ical([{"summary": "No end", "dtstart": start}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert events[0]["end"] is None

    def test_tomorrow_event_returned(self):
        tomorrow = datetime.now() + timedelta(days=1)
        dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0)
        ical_data = _make_ical([{"summary": "Tomorrow", "dtstart": dt}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert len(events) == 1

    def test_past_event_excluded(self):
        yesterday = datetime.now() - timedelta(days=1)
        dt = datetime(yesterday.year, yesterday.month, yesterday.day, 10, 0)
        ical_data = _make_ical([{"summary": "Past", "dtstart": dt}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert len(events) == 0

    def test_far_future_event_excluded(self):
        future = datetime.now() + timedelta(days=3)
        dt = datetime(future.year, future.month, future.day, 10, 0)
        ical_data = _make_ical([{"summary": "Future", "dtstart": dt}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert len(events) == 0

    def test_all_day_event(self):
        today = date.today()
        ical_data = _make_ical([{"summary": "Holiday", "dtstart": today}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert len(events) == 1

    def test_events_sorted_by_start_time(self):
        now = datetime.now()
        ev1 = datetime(now.year, now.month, now.day, 16, 0)
        ev2 = datetime(now.year, now.month, now.day, 9, 0)
        ical_data = _make_ical([
            {"summary": "PM", "dtstart": ev1},
            {"summary": "AM", "dtstart": ev2},
        ])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert events[0]["summary"] == "AM"
        assert events[1]["summary"] == "PM"

    def test_empty_calendar(self):
        ical_data = _make_ical([])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert events == []


class TestFetchAllEvents:
    def test_merges_multiple_calendars(self):
        now = datetime.now()
        ev1 = datetime(now.year, now.month, now.day, 10, 0)
        ev2 = datetime(now.year, now.month, now.day, 14, 0)
        ical1 = _make_ical([{"summary": "Cal1", "dtstart": ev1}])
        ical2 = _make_ical([{"summary": "Cal2", "dtstart": ev2}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.side_effect = [
                mock.Mock(text=ical1, raise_for_status=mock.Mock()),
                mock.Mock(text=ical2, raise_for_status=mock.Mock()),
            ]
            events = fetch_all_events(["https://a.com/1.ics", "https://b.com/2.ics"])

        assert len(events) == 2
        assert events[0]["summary"] == "Cal1"
        assert events[1]["summary"] == "Cal2"

    def test_one_calendar_fails_gracefully(self):
        now = datetime.now()
        ev = datetime(now.year, now.month, now.day, 10, 0)
        ical_data = _make_ical([{"summary": "OK", "dtstart": ev}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.side_effect = [
                Exception("Connection error"),
                mock.Mock(text=ical_data, raise_for_status=mock.Mock()),
            ]
            events = fetch_all_events(["https://bad.com", "https://good.com"])

        assert len(events) == 1
        assert events[0]["summary"] == "OK"

    def test_empty_urls(self):
        events = fetch_all_events([])
        assert events == []


class TestFormatEventText:
    def test_with_end_time(self):
        event = {
            "start": datetime(2026, 3, 24, 9, 0),
            "end": datetime(2026, 3, 24, 10, 0),
            "summary": "ABC",
        }
        assert format_event_text(event) == "09:00-10:00 ABC"

    def test_without_end_time(self):
        event = {
            "start": datetime(2026, 3, 24, 9, 0),
            "end": None,
            "summary": "ABC",
        }
        assert format_event_text(event) == "09:00 ABC"


class TestGetEventPhase:
    def test_notify_phase(self):
        """10 minutes before start → notify"""
        event = {"start": datetime(2026, 3, 24, 9, 0)}
        now = datetime(2026, 3, 24, 8, 50)
        assert get_event_phase(event, now) == "notify"

    def test_notify_phase_5min_before(self):
        """5 minutes before start → notify"""
        event = {"start": datetime(2026, 3, 24, 9, 0)}
        now = datetime(2026, 3, 24, 8, 55)
        assert get_event_phase(event, now) == "notify"

    def test_active_phase_at_start(self):
        """At start time → active"""
        event = {"start": datetime(2026, 3, 24, 9, 0)}
        now = datetime(2026, 3, 24, 9, 0)
        assert get_event_phase(event, now) == "active"

    def test_active_phase_3min_after(self):
        """3 minutes after start → active"""
        event = {"start": datetime(2026, 3, 24, 9, 0)}
        now = datetime(2026, 3, 24, 9, 3)
        assert get_event_phase(event, now) == "active"

    def test_off_at_5min_after(self):
        """5 minutes after start → off"""
        event = {"start": datetime(2026, 3, 24, 9, 0)}
        now = datetime(2026, 3, 24, 9, 5)
        assert get_event_phase(event, now) == "off"

    def test_off_long_before(self):
        """1 hour before start → off"""
        event = {"start": datetime(2026, 3, 24, 9, 0)}
        now = datetime(2026, 3, 24, 8, 0)
        assert get_event_phase(event, now) == "off"

    def test_off_after_event(self):
        """After event → off"""
        event = {"start": datetime(2026, 3, 24, 9, 0)}
        now = datetime(2026, 3, 24, 10, 30)
        assert get_event_phase(event, now) == "off"

    def test_notify_boundary_exact(self):
        """Exactly 10 minutes before → notify"""
        event = {"start": datetime(2026, 3, 24, 9, 0)}
        now = datetime(2026, 3, 24, 8, 50, 0)
        assert get_event_phase(event, now) == "notify"

    def test_off_11min_before(self):
        """11 minutes before → off"""
        event = {"start": datetime(2026, 3, 24, 9, 0)}
        now = datetime(2026, 3, 24, 8, 49)
        assert get_event_phase(event, now) == "off"
