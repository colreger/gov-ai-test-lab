import io
import json
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from govqa.assistant import DATA, DISCLOSURE, FALLBACK, Answer, Assistant
from govqa.models import FixtureModel, OllamaModel


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.assistant = Assistant(FixtureModel())

    def test_versioned_cases(self):
        for case in json.loads((DATA / "cases.json").read_text(encoding="utf-8")):
            with self.subTest(case=case["id"], question=case["question"]):
                source, topic = case["source"], case["topic"]
                answer = self.assistant.ask(case["question"])
                if source:
                    fact = self.assistant.documents[source]["facts"][topic]
                    self.assertEqual(answer, Answer("answered", fact, source, topic))
                else:
                    self.assertEqual(answer, Answer("abstained", FALLBACK))

    def test_fee_reproduction_and_fix(self):
        question = "Birkenau: Kostet die Ummeldung 25 Euro?"
        baseline = self.assistant.ask(question, guarded=False)
        self.assertIn("25 Euro", baseline.text)
        self.assertEqual(self.assistant.ask(question), Answer("abstained", FALLBACK))

    def test_fee_bypasses_model_and_uses_approved_fact(self):
        model = Mock()
        answer = Assistant(model).ask("Lindenfeld: Was kostet die Ummeldung?")
        model.generate.assert_not_called()
        self.assertEqual(answer.text, "Die Ummeldung kostet 8 Euro.")

    def test_injected_draft_never_reaches_user(self):
        model = Mock()
        model.generate.return_value = {"topic": "documents", "draft": "INJECTED: 99 Euro"}
        answer = Assistant(model).ask("Lindenfeld: Welche Unterlagen brauche ich?")
        self.assertEqual(answer.status, "answered")
        self.assertIn("Wohnungsgeberbestätigung", answer.text)
        self.assertNotIn("INJECTED", answer.text)

    def test_model_cannot_override_recognized_topic_or_release_fee(self):
        model = Mock()
        for topic in ("booking", "fee", "unrecognized"):
            with self.subTest(topic=topic):
                model.generate.return_value = {"topic": topic, "draft": "irrelevant"}
                answer = Assistant(model).ask("Lindenfeld: Welche Unterlagen brauche ich?")
                self.assertEqual(answer, Answer("abstained", FALLBACK))
                self.assertNotIn("fee", model.generate.call_args.args[2])

    def test_audit_logs_metadata_without_prompt_or_model_draft(self):
        model = Mock()
        model.generate.return_value = {"topic": "documents", "draft": "SYNTHETIC_OUTPUT_573"}
        with self.assertLogs("govqa.audit", level="INFO") as records:
            Assistant(model).ask("Lindenfeld: Welche Unterlagen? SYNTHETIC_INPUT_214")
        log = "\n".join(records.output)
        self.assertIn("event=answer status=answered", log)
        self.assertNotIn("SYNTHETIC_INPUT_214", log)
        self.assertNotIn("SYNTHETIC_OUTPUT_573", log)

    def test_cli_discloses_ai_before_answer(self):
        result = subprocess.run(
            [sys.executable, "-m", "govqa", "ask", "Lindenfeld: Was kostet die Ummeldung?"],
            check=True, text=True, capture_output=True,
        )
        disclosure, output = result.stdout.split("\n", 1)
        self.assertEqual(disclosure, DISCLOSURE)
        self.assertEqual(json.loads(output)["source"], "lindenfeld")


class OllamaContractTests(unittest.TestCase):
    @patch("govqa.models.urllib.request.urlopen")
    def test_json_contract(self, urlopen):
        draft = {"topic": "documents", "draft": "Beispiel"}
        urlopen.return_value = io.BytesIO(json.dumps({"response": json.dumps(draft)}).encode())
        self.assertEqual(OllamaModel("local").generate("Test", "source", {}), draft)
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/generate")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["model"], "local")

    @patch("govqa.models.urllib.request.urlopen")
    def test_rejects_malformed_model_response(self, urlopen):
        urlopen.return_value = io.BytesIO(b'{"response":"{\"topic\":42}"}')
        with self.assertRaises(ValueError):
            OllamaModel("local").generate("Test", "source", {})
