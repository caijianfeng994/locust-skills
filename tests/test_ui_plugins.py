from locust_skills_ui.plugins import load_monitoring_plugin


class FakeEntryPoint:
    name = "vmp"

    def load(self):
        return "plugin"


def test_load_monitoring_plugin_from_entry_point(monkeypatch):
    monkeypatch.setattr(
        "locust_skills_ui.plugins.entry_points",
        lambda group: [FakeEntryPoint()] if group == "locust_skills_ui.monitoring" else [],
    )

    assert load_monitoring_plugin("vmp") == "plugin"
