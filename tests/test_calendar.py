from datetime import datetime, date, timedelta
from unittest import mock

from icalendar import Calendar, Event

from main import fetch_events, fetch_all_events, format_events_text


def _make_ical(events_data):
    """テスト用のiCalデータを生成する"""
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
        """今日のイベントが返される"""
        now = datetime.now()
        today_event = datetime(now.year, now.month, now.day, 14, 0)
        ical_data = _make_ical([{"summary": "会議", "dtstart": today_event}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert len(events) == 1
        assert events[0]["summary"] == "会議"

    def test_tomorrow_event_returned(self):
        """明日のイベントも返される"""
        tomorrow = datetime.now() + timedelta(days=1)
        dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0)
        ical_data = _make_ical([{"summary": "打ち合わせ", "dtstart": dt}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert len(events) == 1
        assert events[0]["summary"] == "打ち合わせ"

    def test_past_event_excluded(self):
        """昨日のイベントは除外される"""
        yesterday = datetime.now() - timedelta(days=1)
        dt = datetime(yesterday.year, yesterday.month, yesterday.day, 10, 0)
        ical_data = _make_ical([{"summary": "過去", "dtstart": dt}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert len(events) == 0

    def test_far_future_event_excluded(self):
        """2日後以降のイベントは除外される"""
        future = datetime.now() + timedelta(days=3)
        dt = datetime(future.year, future.month, future.day, 10, 0)
        ical_data = _make_ical([{"summary": "来週", "dtstart": dt}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert len(events) == 0

    def test_all_day_event(self):
        """終日イベント（dateオブジェクト）の取得"""
        today = date.today()
        ical_data = _make_ical([{"summary": "休日", "dtstart": today}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert len(events) == 1
        assert events[0]["summary"] == "休日"

    def test_events_sorted_by_start_time(self):
        """イベントが開始時刻順にソートされる"""
        now = datetime.now()
        ev1 = datetime(now.year, now.month, now.day, 16, 0)
        ev2 = datetime(now.year, now.month, now.day, 9, 0)
        ical_data = _make_ical([
            {"summary": "午後", "dtstart": ev1},
            {"summary": "午前", "dtstart": ev2},
        ])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert events[0]["summary"] == "午前"
        assert events[1]["summary"] == "午後"

    def test_empty_calendar(self):
        """イベントなしのカレンダー"""
        ical_data = _make_ical([])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.text = ical_data
            mock_get.return_value.raise_for_status = mock.Mock()
            events = fetch_events("https://example.com/cal.ics")

        assert events == []


class TestFetchAllEvents:
    def test_merges_multiple_calendars(self):
        """複数カレンダーのイベントが統合される"""
        now = datetime.now()
        ev1 = datetime(now.year, now.month, now.day, 10, 0)
        ev2 = datetime(now.year, now.month, now.day, 14, 0)
        ical1 = _make_ical([{"summary": "カレンダー1", "dtstart": ev1}])
        ical2 = _make_ical([{"summary": "カレンダー2", "dtstart": ev2}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.return_value.raise_for_status = mock.Mock()
            mock_get.return_value.text = ical1
            # 2回目の呼び出しでは別データを返す
            mock_get.side_effect = [
                mock.Mock(text=ical1, raise_for_status=mock.Mock()),
                mock.Mock(text=ical2, raise_for_status=mock.Mock()),
            ]
            events = fetch_all_events(["https://a.com/1.ics", "https://b.com/2.ics"])

        assert len(events) == 2
        assert events[0]["summary"] == "カレンダー1"
        assert events[1]["summary"] == "カレンダー2"

    def test_one_calendar_fails_gracefully(self):
        """1つのカレンダー取得が失敗しても他は処理される"""
        now = datetime.now()
        ev = datetime(now.year, now.month, now.day, 10, 0)
        ical_data = _make_ical([{"summary": "OK", "dtstart": ev}])

        with mock.patch("main.requests.get") as mock_get:
            mock_get.side_effect = [
                Exception("接続エラー"),
                mock.Mock(text=ical_data, raise_for_status=mock.Mock()),
            ]
            events = fetch_all_events(["https://bad.com", "https://good.com"])

        assert len(events) == 1
        assert events[0]["summary"] == "OK"

    def test_empty_urls(self):
        """URLリストが空の場合"""
        events = fetch_all_events([])
        assert events == []


class TestFormatEventsText:
    def test_no_events(self):
        """イベントなしの場合"""
        assert format_events_text([]) == "予定なし"

    def test_single_today_event(self):
        """今日のイベント1件"""
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, 14, 30)
        events = [{"start": dt, "summary": "会議"}]
        result = format_events_text(events)
        assert result == "14:30 会議"

    def test_all_day_today_event(self):
        """今日の終日イベント"""
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, 0, 0)
        events = [{"start": dt, "summary": "休日"}]
        result = format_events_text(events)
        assert result == "終日 休日"

    def test_tomorrow_event(self):
        """明日のイベント"""
        tomorrow = datetime.now() + timedelta(days=1)
        dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0)
        events = [{"start": dt, "summary": "打ち合わせ"}]
        result = format_events_text(events)
        assert result == "明日 10:00 打ち合わせ"

    def test_tomorrow_all_day(self):
        """明日の終日イベント"""
        tomorrow = datetime.now() + timedelta(days=1)
        dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0)
        events = [{"start": dt, "summary": "祝日"}]
        result = format_events_text(events)
        assert result == "明日 祝日"

    def test_multiple_events_joined(self):
        """複数イベントは | で結合"""
        now = datetime.now()
        dt1 = datetime(now.year, now.month, now.day, 10, 0)
        dt2 = datetime(now.year, now.month, now.day, 14, 0)
        events = [
            {"start": dt1, "summary": "朝会"},
            {"start": dt2, "summary": "レビュー"},
        ]
        result = format_events_text(events)
        assert result == "10:00 朝会 | 14:00 レビュー"
