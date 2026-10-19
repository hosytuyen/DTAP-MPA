import unittest
from unittest.mock import patch

from agents import OpenAIChatCompletionsModel

from agent.openaisdk.src.agent import _build_model


class ModelRoutingTests(unittest.TestCase):
    def test_default_uses_responses(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(_build_model("gpt-5.4"), "gpt-5.4")

    def test_custom_endpoint_uses_chat_completions(self):
        with patch.dict("os.environ", {
            "OPENAI_BASE_URL": "http://localhost:6008/v1",
            "OPENAI_API_KEY": "dummy",
        }, clear=True):
            model = _build_model("Qwen/Qwen3.6-35B-A3B")
            self.assertIsInstance(model, OpenAIChatCompletionsModel)
            self.assertEqual(model.model, "Qwen/Qwen3.6-35B-A3B")
            self.assertEqual(str(model._client.base_url), "http://localhost:6008/v1/")

    def test_custom_endpoint_can_opt_into_responses(self):
        with patch.dict("os.environ", {
            "OPENAI_BASE_URL": "http://localhost:6008/v1",
            "DTAP_OPENAI_API": "responses",
        }, clear=True):
            self.assertEqual(_build_model("custom"), "custom")

    def test_invalid_api_fails_early(self):
        with patch.dict("os.environ", {"DTAP_OPENAI_API": "invalid"}, clear=True):
            with self.assertRaisesRegex(ValueError, "DTAP_OPENAI_API"):
                _build_model("custom")


if __name__ == "__main__":
    unittest.main()
