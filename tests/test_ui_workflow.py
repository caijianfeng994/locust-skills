from datetime import datetime, timezone
from pathlib import Path

from locust_skills_ui.config import (
    LocustUiConfig,
    ReportsConfig,
    UiConfig,
    VmpConfig,
)
from locust_skills_ui.workflow import WorkflowOptions, run_workflow


class FakeLocustClient:
    def __init__(self):
        self.calls = []

    def wait_until_ready(self, **kwargs):
        self.calls.append(("ready", kwargs))

    def execute(self, **kwargs):
        self.calls.append(("execute", kwargs))
        return {
            "stats": [
                {
                    "name": "Aggregated",
                    "num_requests": 100,
                    "num_failures": 1,
                    "current_rps": 20,
                    "avg_response_time": 30,
                    "median_response_time": 20,
                    "response_time_percentile_0.95": 60,
                    "response_time_percentile_0.99": 90,
                }
            ]
        }

    def download_report(self, path):
        self.calls.append(("report", path))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("<html>report</html>", encoding="utf-8")
        return path


class FakePlugin:
    def collect(self, config, start, end, service_name):
        return {
            "fetch_status": "success",
            "workspace_id": config.workspace_id,
            "time_range": {"start": start, "end": end, "step": config.step},
            "service_metrics": [{"service": service_name}],
            "redis_metrics": [],
            "database_metrics": [],
            "promql_queries": [],
            "empty_results": [],
            "risks": [],
        }


def test_run_workflow_generates_pushes_runs_collects_and_reports(tmp_path: Path):
    curl_file = tmp_path / "request.curl"
    curl_file.write_text(
        "curl --request GET 'http://<service>${service.host_suffix}/go-revenue/api/health'\n",
        encoding="utf-8",
    )
    config = UiConfig(
        locust=LocustUiConfig(
            web_url="https://comm-locust.example",
            deploy_wait_seconds=60,
            api_timeout_seconds=30,
        ),
        vmp=VmpConfig(workspace_id="workspace-1"),
        reports=ReportsConfig(directory=tmp_path / "reports"),
    )
    options = WorkflowOptions(
        curl_file=curl_file,
        duration_seconds=120,
        users=200,
        spawn_rate=20,
        branch="main",
        tag="locust-test",
        context_path=tmp_path / "rag_context.json",
        locustfile_path=tmp_path / "locustfile.py",
    )
    git_calls = []
    sleeps = []
    client = FakeLocustClient()
    timestamps = iter([
        datetime(2026, 7, 22, 8, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 22, 8, 2, tzinfo=timezone.utc),
    ])

    result = run_workflow(
        options,
        config,
        locust_client=client,
        monitoring_plugin=FakePlugin(),
        publisher=lambda **kwargs: git_calls.append(kwargs),
        sleep=sleeps.append,
        now=lambda: next(timestamps),
    )

    assert sleeps == [60]
    assert git_calls[0]["tag"] == "locust-test"
    assert client.calls[1][0] == "execute"
    assert client.calls[1][1]["duration_seconds"] == 120
    assert result.report_path.is_file()
    assert (tmp_path / "reports/locust_ui_report.html").is_file()
    assert (tmp_path / "reports/locust_ui_stats.json").is_file()
    assert (tmp_path / "reports/vmp_context.json").is_file()
