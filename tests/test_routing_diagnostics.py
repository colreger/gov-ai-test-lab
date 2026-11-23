import unittest
from unittest.mock import Mock
from govqa.assistant import Assistant, FALLBACK


class RoutingDiagnosticTests(unittest.TestCase):
    def test_two_open_cases_keep_source_and_topic_safety(self):
        for question in ('Lindenfeld: Brauche ich einen Ausweis?', 'Auenbrück: Brauche ich einen Reisepass?'):
            for topic, reason in [('documents', 'approved_source'), ('unknown', 'topic_not_in_context'), ('booking', 'topic_mismatch')]:
                with self.subTest(question=question, topic=topic):
                    model = Mock()
                    model.generate.return_value = {'topic': topic, 'draft': 'PRIVATE_DRAFT'}
                    assistant = Assistant(model)
                    with self.assertLogs('govqa.audit', level='INFO') as logs:
                        answer = assistant.ask(question)
                    self.assertEqual(assistant.last_diagnostic['reason'], reason)
                    self.assertEqual(answer.status, 'answered' if topic == 'documents' else 'abstained')
                    if topic != 'documents':
                        self.assertEqual(answer.text, FALLBACK)
                    self.assertNotIn(question, str(logs.output))
                    self.assertNotIn('PRIVATE_DRAFT', str(logs.output))

    def test_contract_error_is_identified_without_payload(self):
        model = Mock()
        model.generate.side_effect = ValueError('PRIVATE_PAYLOAD')
        assistant = Assistant(model)
        with self.assertLogs('govqa.audit', level='INFO') as logs:
            with self.assertRaises(ValueError):
                assistant.ask('Lindenfeld: Brauche ich einen Ausweis?')
        self.assertEqual(assistant.last_diagnostic['reason'], 'model_contract_rejected')
        self.assertNotIn('PRIVATE_PAYLOAD', str(logs.output))
