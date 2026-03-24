from datetime import datetime, date, timedelta
from unittest import mock

from icloud_calendar import fetch_icloud_events, _parse_caldav_event


def _make_mock_vevent(summary, dtstart):
    """CalDAVイベントのモックを作成する"""
    vevent = mock.Mock()
    vevent.summary.value = summary
    vevent.dtstart.value = dtstart
    has_summary = True

    def hasattr_side_effect(name):
        if name == "summary":
            return has_summary
        return True

    event = mock.Mock()
    event.vobject_instance.vevent = vevent
    # hasattr対応
    type(vevent).summary = mock.PropertyMock(return_value=mock.Mock(value=summary))
    return event


def _make_mock_vevent_no_summary(dtstart):
    """summaryなしのCalDAVイベントモック"""
    vevent = mock.Mock(spec=[])
    vevent.dtstart = mock.Mock()
    vevent.dtstart.value = dtstart

    event = mock.Mock()
    event.vobject_instance.vevent = vevent
    return event


class TestParseCalDavEvent:
    def test_datetime_event(self):
        """datetime型のイベントをパースできる"""
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, 14, 0)
        event = _make_mock_vevent("会議", dt)
        result = _parse_caldav_event(event)
        assert result is not None
        assert result["summary"] == "会議"
        assert result["start"] == dt

    def test_date_event(self):
        """date型（終日イベント）をパースできる"""
        today = date.today()
        event = _make_mock_vevent("休日", today)
        result = _parse_caldav_event(event)
        assert result is not None
        assert result["summary"] == "休日"
        assert result["start"].date() == today

    def test_past_event_excluded(self):
        """昨日のイベントはNoneを返す"""
        yesterday = datetime.now() - timedelta(days=2)
        dt = datetime(yesterday.year, yesterday.month, yesterday.day, 10, 0)
        event = _make_mock_vevent("過去", dt)
        result = _parse_caldav_event(event)
        assert result is None

    def test_future_event_excluded(self):
        """3日後のイベントはNoneを返す"""
        future = datetime.now() + timedelta(days=3)
        dt = datetime(future.year, future.month, future.day, 10, 0)
        event = _make_mock_vevent("未来", dt)
        result = _parse_caldav_event(event)
        assert result is None

    def test_tomorrow_event_included(self):
        """明日のイベントは含まれる"""
        tomorrow = datetime.now() + timedelta(days=1)
        dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0)
        event = _make_mock_vevent("明日の予定", dt)
        result = _parse_caldav_event(event)
        assert result is not None
        assert result["summary"] == "明日の予定"

    def test_no_summary(self):
        """summaryがないイベントでもパースできる"""
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, 14, 0)
        event = _make_mock_vevent_no_summary(dt)
        result = _parse_caldav_event(event)
        assert result is not None
        assert result["summary"] == ""

    def test_timezone_aware_datetime(self):
        """タイムゾーン付きdatetimeのtzinfoが除去される"""
        from datetime import timezone
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, 14, 0, tzinfo=timezone.utc)
        event = _make_mock_vevent("UTC会議", dt)
        result = _parse_caldav_event(event)
        assert result is not None
        assert result["start"].tzinfo is None


class TestFetchIcloudEvents:
    def test_fetches_from_all_calendars(self):
        """全カレンダーからイベントを取得して統合する"""
        now = datetime.now()
        ev1 = _make_mock_vevent("仕事", datetime(now.year, now.month, now.day, 10, 0))
        ev2 = _make_mock_vevent("個人", datetime(now.year, now.month, now.day, 15, 0))

        mock_cal1 = mock.Mock()
        mock_cal1.name = "仕事"
        mock_cal1.search.return_value = [ev1]

        mock_cal2 = mock.Mock()
        mock_cal2.name = "個人"
        mock_cal2.search.return_value = [ev2]

        with mock.patch("icloud_calendar.caldav.DAVClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.principal.return_value.calendars.return_value = [mock_cal1, mock_cal2]
            events = fetch_icloud_events("user@icloud.com", "xxxx-xxxx")

        assert len(events) == 2
        assert events[0]["summary"] == "仕事"
        assert events[1]["summary"] == "個人"

    def test_one_calendar_fails_gracefully(self):
        """1つのカレンダーが失敗しても他は取得できる"""
        now = datetime.now()
        ev = _make_mock_vevent("OK", datetime(now.year, now.month, now.day, 10, 0))

        mock_cal1 = mock.Mock()
        mock_cal1.name = "壊れたカレンダー"
        mock_cal1.search.side_effect = Exception("エラー")

        mock_cal2 = mock.Mock()
        mock_cal2.name = "正常"
        mock_cal2.search.return_value = [ev]

        with mock.patch("icloud_calendar.caldav.DAVClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.principal.return_value.calendars.return_value = [mock_cal1, mock_cal2]
            events = fetch_icloud_events("user@icloud.com", "xxxx-xxxx")

        assert len(events) == 1
        assert events[0]["summary"] == "OK"

    def test_empty_calendars(self):
        """カレンダーにイベントがない場合"""
        mock_cal = mock.Mock()
        mock_cal.name = "空"
        mock_cal.search.return_value = []

        with mock.patch("icloud_calendar.caldav.DAVClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.principal.return_value.calendars.return_value = [mock_cal]
            events = fetch_icloud_events("user@icloud.com", "xxxx-xxxx")

        assert events == []

    def test_events_sorted_by_start_time(self):
        """イベントが開始時刻順にソートされる"""
        now = datetime.now()
        ev1 = _make_mock_vevent("午後", datetime(now.year, now.month, now.day, 16, 0))
        ev2 = _make_mock_vevent("午前", datetime(now.year, now.month, now.day, 9, 0))

        mock_cal = mock.Mock()
        mock_cal.name = "テスト"
        mock_cal.search.return_value = [ev1, ev2]

        with mock.patch("icloud_calendar.caldav.DAVClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.principal.return_value.calendars.return_value = [mock_cal]
            events = fetch_icloud_events("user@icloud.com", "xxxx-xxxx")

        assert events[0]["summary"] == "午前"
        assert events[1]["summary"] == "午後"
