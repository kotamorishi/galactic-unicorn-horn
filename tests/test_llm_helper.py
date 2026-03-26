from datetime import datetime
from unittest import mock

from llm_helper import detect_ollama, select_model, format_event_with_llm
from main import get_display_text, format_event_text


class TestDetectOllama:
    def test_detected_when_reachable(self):
        with mock.patch("llm_helper.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            result = detect_ollama("http://localhost:11434")
        assert result == "http://localhost:11434"

    def test_none_when_unreachable(self):
        with mock.patch("llm_helper.requests.get") as mock_get:
            mock_get.side_effect = ConnectionError("refused")
            result = detect_ollama("http://localhost:11434")
        assert result is None

    def test_none_when_non_200(self):
        with mock.patch("llm_helper.requests.get") as mock_get:
            mock_get.return_value.status_code = 500
            result = detect_ollama("http://localhost:11434")
        assert result is None

    def test_uses_default_url_when_none(self):
        with mock.patch("llm_helper.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            result = detect_ollama(None)
        assert result == "http://localhost:11434"


class TestSelectModel:
    def test_selects_preferred_model(self):
        with mock.patch("llm_helper.requests.get") as mock_get:
            mock_get.return_value.raise_for_status = mock.Mock()
            mock_get.return_value.json.return_value = {
                "models": [
                    {"name": "llama3.2:3b"},
                    {"name": "qwen2.5:3b"},
                ]
            }
            result = select_model("http://localhost:11434", "qwen2.5")
        assert result == "qwen2.5:3b"

    def test_falls_back_to_first_model(self):
        with mock.patch("llm_helper.requests.get") as mock_get:
            mock_get.return_value.raise_for_status = mock.Mock()
            mock_get.return_value.json.return_value = {
                "models": [{"name": "llama3.2:3b"}]
            }
            result = select_model("http://localhost:11434", "nonexistent")
        assert result == "llama3.2:3b"

    def test_returns_none_when_no_models(self):
        with mock.patch("llm_helper.requests.get") as mock_get:
            mock_get.return_value.raise_for_status = mock.Mock()
            mock_get.return_value.json.return_value = {"models": []}
            result = select_model("http://localhost:11434")
        assert result is None


class TestFormatEventWithLLM:
    def test_returns_formatted_text(self):
        with mock.patch("llm_helper.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            mock_post.return_value.json.return_value = {
                "message": {"content": "9時から打ち合わせです"}
            }
            result = format_event_with_llm(
                "http://localhost:11434", "qwen2.5:3b", "09:00-10:00 打ち合わせ"
            )
        assert result == "9時から打ち合わせです"

    def test_rejects_overly_long_response(self):
        with mock.patch("llm_helper.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            mock_post.return_value.json.return_value = {
                "message": {"content": "a" * 81}
            }
            result = format_event_with_llm(
                "http://localhost:11434", "qwen2.5:3b", "09:00 Test"
            )
        assert result is None

    def test_returns_none_on_error(self):
        with mock.patch("llm_helper.requests.post") as mock_post:
            mock_post.side_effect = ConnectionError("refused")
            result = format_event_with_llm(
                "http://localhost:11434", "qwen2.5:3b", "09:00 Test"
            )
        assert result is None

    def test_sends_correct_payload(self):
        with mock.patch("llm_helper.requests.post") as mock_post:
            mock_post.return_value.raise_for_status = mock.Mock()
            mock_post.return_value.json.return_value = {
                "message": {"content": "test"}
            }
            format_event_with_llm(
                "http://localhost:11434", "mymodel", "09:00 Meeting"
            )
        payload = mock_post.call_args[1]["json"]
        assert payload["model"] == "mymodel"
        assert payload["stream"] is False
        assert len(payload["messages"]) == 2
        assert payload["messages"][1]["content"] == "09:00 Meeting"


class TestGetDisplayText:
    def _make_event(self, summary="Meeting", hour=9):
        return {
            "start": datetime(2026, 3, 25, hour, 0),
            "end": datetime(2026, 3, 25, hour + 1, 0),
            "summary": summary,
        }

    def test_plain_text_when_no_llm(self):
        event = self._make_event()
        result = get_display_text(event, None, None, {})
        assert result == format_event_text(event)

    def test_uses_llm_when_available(self):
        event = self._make_event("打ち合わせ")
        with mock.patch("main.format_event_with_llm") as mock_llm:
            mock_llm.return_value = "9時から打ち合わせです"
            result = get_display_text(
                event, "http://localhost:11434", "qwen2.5:3b", {}
            )
        assert result == "9時から打ち合わせです"

    def test_falls_back_on_llm_failure(self):
        event = self._make_event()
        with mock.patch("main.format_event_with_llm") as mock_llm:
            mock_llm.return_value = None
            result = get_display_text(
                event, "http://localhost:11434", "qwen2.5:3b", {}
            )
        assert result == format_event_text(event)

    def test_uses_cache(self):
        event = self._make_event("打ち合わせ")
        cache_key = (event["start"], event["summary"])
        cache = {cache_key: "キャッシュされたテキスト"}
        with mock.patch("main.format_event_with_llm") as mock_llm:
            result = get_display_text(
                event, "http://localhost:11434", "qwen2.5:3b", cache
            )
        mock_llm.assert_not_called()
        assert result == "キャッシュされたテキスト"

    def test_populates_cache(self):
        event = self._make_event("打ち合わせ")
        cache = {}
        with mock.patch("main.format_event_with_llm") as mock_llm:
            mock_llm.return_value = "9時から打ち合わせです"
            get_display_text(
                event, "http://localhost:11434", "qwen2.5:3b", cache
            )
        cache_key = (event["start"], event["summary"])
        assert cache[cache_key] == "9時から打ち合わせです"
