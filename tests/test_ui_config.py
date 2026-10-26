from pathlib import Path

import pytest

from locust_skills_ui.config import load_config
from locust_skills_ui.duration import parse_duration


@pytest.mark.parametrize(
    ("value", "seconds"),
    [("30s", 30.0), ("2m", 120.0), ("1.5h", 5400.0)],
)
def test_parse_duration(value: str, seconds: float):
    assert parse_duration(value) == seconds


@pytest.mark.parametrize("value", ["", "0m", "-1s", "2d", "abc"])
def test_parse_duration_rejects_invalid_values(value: str):
    with pytest.raises(ValueError):
        parse_duration(value)


def test_load_ui_config(tmp_path: Path):
    path = tmp_path / "locust-skills-ui.yaml"
    path.write_text(
        """
locust:
  web_url: https://locust.example
  deploy_wait_seconds: 60
  api_timeout_seconds: 30
vmp:
  workspace_id: workspace-1
  region: cn-beijing
  step: 60s
  service_queries:
    - up{service="$service"}
reports:
  directory: reports
""",
        encoding="utf-8",
    )

    config = load_config(path)

    assert config.locust.web_url == "https://locust.example"
    assert config.locust.deploy_wait_seconds == 60
    assert config.vmp.workspace_id == "workspace-1"
    assert config.vmp.service_queries == ('up{service="$service"}',)
    assert config.reports.directory == Path("reports")
