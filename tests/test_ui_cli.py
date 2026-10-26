from typer.testing import CliRunner

from locust_skills_ui.cli import app


runner = CliRunner()


def test_ui_cli_exposes_full_workflow_options():
    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0
    for option in (
        "--yapi-url",
        "--curl-file",
        "--duration",
        "--users",
        "--spawn-rate",
        "--branch",
        "--tag",
        "--config",
    ):
        assert option in result.output
