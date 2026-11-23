import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
TOPICS = {
    "fee": r"geb[uü]h?r|kost|preis|bezahl|zahle?n|euro|€|gratis|\beur\b",
    "documents": r"unterlag|dokument|mitbring|mit.?nehmen|ausweis|pass\b|papiere|bescheinigung",
    "deadline": r"frist|frisst|bis wann|wie (?:viel|viele|lange)|tage[n]?\b|zu sp[aä]t",
    "booking": r"termin|termien|buch|anmeld.*slot",
}
FALLBACK = "Dazu liegt in den freigegebenen Quellen keine eindeutige Information vor."
DISCLOSURE = "Sie interagieren mit einem KI-Assistenten in einer fiktiven Testumgebung."
AUDIT = logging.getLogger("govqa.audit")


@dataclass(frozen=True)
class Answer:
    status: str
    text: str
    source: str | None = None
    topic: str | None = None


def load_documents(path=DATA / "documents.json"):
    return {doc["id"]: doc for doc in json.loads(path.read_text(encoding="utf-8"))}


def matching_topics(question):
    return [topic for topic, pattern in TOPICS.items() if re.search(pattern, question.casefold())]


def select_document(question, documents):
    normalized = unicodedata.normalize("NFKC", question).casefold().replace("ü", "ue")
    matches = [key for key in documents if re.search(rf"\b{re.escape(key)}\b", normalized)]
    return documents[matches[0]] if len(matches) == 1 else None


class Assistant:
    def __init__(self, model, documents=None):
        self.model = model
        self.documents = load_documents() if documents is None else documents

    def ask(self, question, *, guarded=True):
        self.last_diagnostic = {"reason": "started"}
        answer = self._ask(question, guarded=guarded)
        AUDIT.info("event=answer status=%s guarded=%s", answer.status, guarded)
        return answer

    def _diagnose(self, reason, topic=None):
        # Never retain the prompt, draft or arbitrary model strings.
        self.last_diagnostic = {"reason": reason, "model_topic": topic if topic in TOPICS or topic == "unknown" else "invalid"}
        AUDIT.info("event=routing reason=%s model_topic=%s", reason, self.last_diagnostic["model_topic"])

    def _ask(self, question, *, guarded):
        document = select_document(question, self.documents)
        if document is None:
            self._diagnose("source_unresolved")
            return Answer("abstained", FALLBACK)

        topics = matching_topics(question)
        if guarded and len(topics) > 1:
            self._diagnose("multiple_topics")
            return Answer("abstained", FALLBACK)
        if guarded and topics == ["fee"]:
            self._diagnose("fee_source_only")
            return self._render(document, "fee")

        context = dict(document["facts"])
        if guarded:
            context.pop("fee", None)
        try:
            result = self.model.generate(question, document["id"], context)
        except ValueError:
            self._diagnose("model_contract_rejected")
            raise
        if not guarded:
            self._diagnose("unguarded_draft", result["topic"])
            return Answer("draft", result["draft"], document["id"], result["topic"])
        topic = result["topic"]
        if topic not in context or (topics and topic != topics[0]):
            self._diagnose("topic_not_in_context" if topic not in context else "topic_mismatch", topic)
            return Answer("abstained", FALLBACK)
        self._diagnose("approved_source", topic)
        return self._render(document, topic)

    @staticmethod
    def _render(document, topic):
        fact = document["facts"].get(topic)
        if fact is None:
            return Answer("abstained", FALLBACK)
        return Answer("answered", fact, document["id"], topic)
