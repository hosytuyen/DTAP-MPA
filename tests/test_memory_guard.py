import unittest
from types import SimpleNamespace
from unittest.mock import patch

from utils.memory_guard import check_memory_before_launch


class MemoryGuardTests(unittest.TestCase):
    def test_configured_threshold_and_boundary(self):
        with patch.dict("os.environ", {
            "DTAP_MEMORY_REQUIRED_GB": "2", "DTAP_MEMORY_RESERVE_GB": "1",
        }), patch("utils.memory_guard.psutil.virtual_memory") as memory:
            memory.return_value = SimpleNamespace(available=3 * 1024**3)
            check_memory_before_launch()
            memory.return_value = SimpleNamespace(available=2.9 * 1024**3)
            with self.assertRaises(RuntimeError):
                check_memory_before_launch()

    def test_explicit_arguments_override_environment(self):
        with patch.dict("os.environ", {"DTAP_MEMORY_REQUIRED_GB": "64"}), patch(
            "utils.memory_guard.psutil.virtual_memory",
            return_value=SimpleNamespace(available=3 * 1024**3),
        ):
            check_memory_before_launch(required_gb=2, reserve_gb=1)

    def test_invalid_thresholds(self):
        for value in (-1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                check_memory_before_launch(required_gb=value, reserve_gb=1)
