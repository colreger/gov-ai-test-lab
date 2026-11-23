import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

from govqa.models import NvidiaModel


class NvidiaAdapterTests(unittest.TestCase):
    def model(self):
        return NvidiaModel("test-model", "grounded", "not-a-real-key")

    def test_structured_request_and_usage_without_network(self):
        model = self.model()
        envelope = {"choices": [{"message": {"content": '{"topic":"documents","draft":"Approved text"}'}}],
                    "usage": {"prompt_tokens": 12, "completion_tokens": 4}}
        with patch.object(model, "request", return_value=envelope) as sender:
            answer = model.generate("Synthetic question", "fictional", {"documents": "Approved text"})
        payload = json.loads(sender.call_args.args[0].data)
        self.assertEqual(answer["topic"], "documents")
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(model.last_usage, {"prompt_eval_count": 12, "eval_count": 4})
        self.assertNotIn("not-a-real-key", json.dumps(model.configuration()))

    def test_malformed_model_payload_rejected(self):
        model = self.model()
        for content in ('{"topic":42,"draft":"text"}', 'not json', '{"topic":"whole answer sentence","draft":"text"}', '{"topic":"documents","draft":"text","extra":true}'):
            with patch.object(model, "request", return_value={"choices": [{"message": {"content": content}}]}):
                with self.assertRaisesRegex(ValueError, "Invalid model answer format"):
                    model.generate("Synthetic question", "fictional", {"documents": "Approved text"})

    def test_429_retry_count_and_backoff_are_bounded(self):
        clock = [0.0]
        sleeps = []
        def sleep(delay):
            sleeps.append(delay)
            clock[0] += delay
        errors = [HTTPError("https://example.invalid", 429, "limited", {}, None) for _ in range(3)]
        with patch("govqa.models.time.monotonic", side_effect=lambda: clock[0]), \
             patch("govqa.models.time.sleep", side_effect=sleep), \
             patch("govqa.models.urllib.request.urlopen", side_effect=errors) as sender:
            with self.assertRaises(HTTPError):
                self.model().request(Request("https://example.invalid"))
        self.assertEqual(sender.call_count, 3)
        self.assertEqual(sleeps, [8.0, 16.0])

    def test_retry_after_over_sixty_seconds_is_not_slept(self):
        error = HTTPError("https://example.invalid", 429, "limited", {"Retry-After": "61"}, None)
        with patch("govqa.models.time.monotonic", return_value=0), \
             patch("govqa.models.time.sleep") as sleep, \
             patch("govqa.models.urllib.request.urlopen", side_effect=error) as sender:
            with self.assertRaises(HTTPError):
                self.model().request(Request("https://example.invalid"))
        self.assertEqual(sender.call_count, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
