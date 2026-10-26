import importlib.util
import py_compile
import tempfile
import unittest
from pathlib import Path


GENERATOR_PATH = Path(__file__).with_name("generate_locustfile_from_rag.py")


def load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_locustfile_from_rag", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GenerateLocustfileFromRagTest(unittest.TestCase):
    def setUp(self):
        self.generator = load_generator_module()

    def test_infer_host_from_path_uses_first_service_segment(self):
        host = self.generator.infer_host_from_path("/go-revenue/activity/summer2026")

        self.assertEqual(host, "http://<service>${service.host_suffix}")

    def test_render_locustfile_generates_get_and_post_tasks(self):
        rag_context = {
            "fetch_status": "success",
            "interfaces": [
                {
                    "fetch_status": "success",
                    "interface_name": "判断抽奖资格",
                    "method": "GET",
                    "path": "/go-revenue/activity/summer2026/draw-order/check",
                    "request": {
                        "query_params": [{"name": "orderId", "example": "order-1"}],
                        "headers": [{"name": "uid", "example": "user-1"}],
                    },
                },
                {
                    "fetch_status": "success",
                    "interface_name": "执行抽奖",
                    "method": "POST",
                    "path": "/go-revenue/activity/summer2026/draw-order",
                    "request": {
                        "query_params": [{"name": "orderId", "example": "order-1"}],
                        "headers": [{"name": "Content-Type", "example": "application/json"}],
                        "body_fields": [{"name": "source", "example": "summer2026"}],
                    },
                },
            ],
        }

        content = self.generator.render_locustfile(rag_context)

        self.assertIn('host = "http://<service>${service.host_suffix}"', content)
        self.assertIn("def task_1_draw_order_check", content)
        self.assertIn("self.client.get", content)
        self.assertIn('name="判断抽奖资格"', content)
        self.assertIn("catch_response=True", content)
        self.assertIn("def task_2_draw_order", content)
        self.assertIn("self.client.post", content)
        self.assertIn("json=json_data", content)

    def test_skill_generator_always_generates_lifecycle_methods(self):
        rag_context = {
            "fetch_status": "success",
            "interfaces": [
                {
                    "fetch_status": "success",
                    "interface_name": "查询用户",
                    "method": "GET",
                    "path": "/user/detail",
                    "request": {
                        "query_params": [{"name": "userId", "example": ""}],
                        "headers": [],
                    },
                }
            ],
        }

        content = self.generator.render_locustfile(rag_context)

        self.assertIn("def load_test_data(cls):", content)
        self.assertIn("def on_start(self):", content)
        self.assertIn("./config/userId.csv", content)

    def test_render_locustfile_skips_failed_or_incomplete_interfaces(self):
        rag_context = {
            "fetch_status": "partial",
            "interfaces": [
                {
                    "fetch_status": "failed",
                    "interface_name": "失败接口",
                    "fetch_error": "YApi 读取失败",
                },
                {
                    "fetch_status": "success",
                    "interface_name": "缺少路径",
                    "method": "GET",
                    "path": "",
                },
            ],
        }

        content = self.generator.render_locustfile(rag_context)

        self.assertIn("跳过接口：失败接口，原因：YApi 读取失败", content)
        self.assertIn("跳过接口：缺少路径，原因：缺少 method 或 path", content)
        self.assertNotIn("@task", content)

    def test_write_locustfile_creates_compilable_python(self):
        rag_context = {
            "fetch_status": "success",
            "interfaces": [
                {
                    "fetch_status": "success",
                    "interface_name": "查询用户抽奖记录",
                    "method": "GET",
                    "path": "/go-revenue/activity/summer2026/draw-order/record",
                    "request": {"query_params": [], "headers": []},
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "locustfile.py"
            self.generator.write_locustfile(self.generator.render_locustfile(rag_context), output)
            py_compile.compile(str(output), doraise=True)

        self.assertTrue(True)

    def test_write_locustfile_renames_existing_file_with_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "locustfile.py"
            output.write_text("# old locustfile\n", encoding="utf-8")

            backup_path = self.generator.write_locustfile(
                "from locust import HttpUser\n",
                output,
                timestamp="20260714-181600",
            )

            self.assertEqual(backup_path, Path(temp_dir) / "locustfile_20260714-181600.py")
            self.assertEqual(backup_path.read_text(encoding="utf-8"), "# old locustfile\n")
            self.assertEqual(output.read_text(encoding="utf-8"), "from locust import HttpUser\n")


if __name__ == "__main__":
    unittest.main()
