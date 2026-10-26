from pathlib import Path
import tomllib

from setuptools import find_namespace_packages


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UI_SKILL_ROOT = PROJECT_ROOT / "skills" / "locust-skills-ui"
UI_COMMAND_FILE = PROJECT_ROOT / ".cursor" / "commands" / "locust_skills_ui.md"


def test_main_package_registers_both_cli_entries_and_limits_discovery():
    config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert config["project"]["scripts"]["locust-skills-ui"] == "locust_skills_ui.cli:app"
    includes = config["tool"]["setuptools"]["packages"]["find"]["include"]
    assert "locust_skills_ui" in includes
    assert "locust_skills_ui.*" not in includes

    discovered = find_namespace_packages(
        "src",
        include=includes,
    )
    assert "locust_skills_ui" in discovered
    assert not any(
        package.startswith("locust_skills_ui.vmp-monitoring") for package in discovered
    )


def test_vmp_plugin_declares_monitoring_entry_point():
    config = tomllib.loads(
        (PROJECT_ROOT / "plugins/vmp/pyproject.toml").read_text(encoding="utf-8")
    )

    entry_points = config["project"]["entry-points"]["locust_skills_ui.monitoring"]
    assert entry_points["vmp"] == "locust_skills_ui_vmp.plugin:plugin"


def test_locust_skills_ui_is_registered_as_project_skill():
    skill_file = UI_SKILL_ROOT / "SKILL.md"

    assert skill_file.exists()
    content = skill_file.read_text(encoding="utf-8")
    assert "name: locust-skills-ui" in content
    assert "/locust_skills_ui" in content


def test_locust_skills_ui_cursor_command_is_registered():
    assert UI_COMMAND_FILE.exists()
    content = UI_COMMAND_FILE.read_text(encoding="utf-8")
    assert "# locust_skills_ui" in content
    assert "locust-skills-ui run" in content
