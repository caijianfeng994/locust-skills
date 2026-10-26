from pathlib import Path

import pytest

from locust_skills_ui.locust_api import LocustUiClient


class FakeResponse:
    def __init__(self, *, json_data=None, content=b"", status_code=200):
        self._json_data = json_data
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


class FakeSession:
    def __init__(self):
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if url.endswith("/stats/report?theme=light"):
            return FakeResponse(content=b"<html>report</html>")
        return FakeResponse(json_data={"state": "running", "stats": []})

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return FakeResponse(json_data={"success": True})


def test_locust_client_starts_stops_and_downloads_report(tmp_path: Path):
    session = FakeSession()
    client = LocustUiClient("https://locust.example", timeout=5, session=session)

    client.reset_stats()
    client.start(users=20, spawn_rate=5, host="http://service${service.host_suffix}")
    stats = client.get_stats()
    client.stop()
    report_path = client.download_report(tmp_path / "report.html")

    assert stats["state"] == "running"
    assert report_path.read_bytes() == b"<html>report</html>"
    assert session.calls == [
        ("GET", "https://locust.example/stats/reset", {"timeout": 5}),
        (
            "POST",
            "https://locust.example/swarm",
            {
                "data": {
                    "user_count": "20",
                    "spawn_rate": "5",
                    "host": "http://service${service.host_suffix}",
                },
                "timeout": 5,
            },
        ),
        ("GET", "https://locust.example/stats/requests", {"timeout": 5}),
        ("GET", "https://locust.example/stop", {"timeout": 5}),
        ("GET", "https://locust.example/stats/report?theme=light", {"timeout": 5}),
    ]


def test_execute_stops_test_when_waiting_fails():
    session = FakeSession()
    client = LocustUiClient("https://locust.example", timeout=5, session=session)

    def fail_sleep(_seconds):
        raise RuntimeError("interrupted")

    with pytest.raises(RuntimeError, match="interrupted"):
        client.execute(
            users=20,
            spawn_rate=5,
            host="http://service${service.host_suffix}",
            duration_seconds=120,
            sleep=fail_sleep,
        )

    assert ("GET", "https://locust.example/stop", {"timeout": 5}) in session.calls
