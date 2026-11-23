import argparse
import hashlib
import json
import logging
import math
import os
import re
import statistics
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from .assistant import DATA, DISCLOSURE, FALLBACK, Answer, Assistant
from .models import FixtureModel, NvidiaModel, OllamaModel


AMOUNT = re.compile(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(?:Euro\b|EUR\b|€)", re.IGNORECASE)


def measure_answer(answer, expected, source, topic, documents):
    fact = documents.get(answer.source, {}).get("facts", {}).get(answer.topic)
    actual_amounts = {float(value.replace(",", ".")) for value in AMOUNT.findall(answer.text)}
    expected_amounts = {float(value.replace(",", ".")) for value in AMOUNT.findall(expected)} if source else set()
    return {
        "correct_text": answer.text == expected,
        "correct_source": answer.source == source,
        "correct_topic": answer.topic == topic,
        "exact_source_match": answer.text == fact if answer.status != "abstained" else None,
        "unsupported_fee_amount": (
            answer.status != "abstained" and (topic == "fee" or answer.topic == "fee")
            and bool(actual_amounts - expected_amounts)
        ),
    }


def summarize(entries):
    timings = sorted(row["latency_ms"] for row in entries)
    scored = [row for row in entries if row["checks"]["exact_source_match"] is not None]
    usage = [row["model_usage"] for row in entries if row["model_usage"] is not None]
    return {
        "passed": sum(row["passed"] for row in entries),
        "errors": sum(row["error"] is not None for row in entries),
        "total": len(entries),
        "exact_source_matches": sum(row["checks"]["exact_source_match"] for row in scored),
        "non_abstained": len(scored),
        "flagged_fee_outputs": sum(row["checks"]["unsupported_fee_amount"] for row in entries),
        "median_ms": statistics.median(timings),
        "p95_ms": timings[math.ceil(0.95 * len(timings)) - 1],
        "model_calls_with_telemetry": len(usage),
        "usage_totals": {
            key: sum(item[key] for item in usage)
            for key in ("prompt_eval_count", "eval_count", "total_duration")
            if usage and all(key in item for item in usage)
        },
    }


def evaluate(assistant, runs):
    cases_path = DATA / "cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    rows = []
    groups = defaultdict(list)
    for case in cases:
        source = case["source"]
        topic = case["topic"]
        expected = assistant.documents[source]["facts"][topic] if source else FALLBACK
        for run in range(1, runs + 1):
            for guarded in (False, True):
                if hasattr(assistant.model, "last_usage"):
                    assistant.model.last_usage = None
                start = time.perf_counter()
                error = None
                try:
                    answer = assistant.ask(case["question"], guarded=guarded)
                except (OSError, ValueError, KeyError) as exc:
                    error = str(exc.code) if hasattr(exc, "code") else type(exc).__name__
                    answer = Answer("error", "")
                elapsed_ms = (time.perf_counter() - start) * 1000
                checks = measure_answer(answer, expected, source, topic, assistant.documents)
                passed = error is None and all(checks[key] for key in ("correct_text", "correct_source", "correct_topic"))
                row = dict(case_id=case["id"], group=case["group"], run=run, guarded=guarded,
                           passed=passed, error=error, latency_ms=round(elapsed_ms, 2), checks=checks,
                           model_usage=getattr(assistant.model, "last_usage", None),
                           answer=asdict(answer))
                rows.append(row)
                groups[case["group"], guarded].append(row)
    summary = [
        dict(group=group, guarded=guarded, **summarize(entries))
        for (group, guarded), entries in groups.items()
    ]
    totals = [
        dict(guarded=guarded, **summarize([row for row in rows if row["guarded"] == guarded]))
        for guarded in (False, True)
    ]
    return {
        "model": assistant.model.name,
        "model_configuration": (
            assistant.model.configuration() if isinstance(assistant.model, NvidiaModel) else None
        ),
        "runs": runs,
        "case_count": len(cases),
        "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "documents_sha256": hashlib.sha256((DATA / "documents.json").read_bytes()).hexdigest(),
        "summary": summary,
        "totals": totals,
        "results": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=DISCLOSURE)
    parser.add_argument("--model", help="Lokales Ollama-Modell. Standard: deterministische Fixture.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    ask = subcommands.add_parser("ask")
    ask.add_argument("question")
    evaluate_command = subcommands.add_parser("evaluate")
    evaluate_command.add_argument("--compare-model", action="append", default=[],
                                  help="Zusätzliches lokales Ollama-Modell (wiederholbar).")
    evaluate_command.add_argument("--nvidia-model", help="Vergleicht zwei Promptvarianten über NVIDIA.")
    evaluate_command.add_argument("--runs", type=int, default=1)
    evaluate_command.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "evaluate" and args.runs < 1:
        parser.error("--runs muss mindestens 1 sein.")
    if args.command == "evaluate" and args.nvidia_model and not os.getenv("NVIDIA_API_KEY"):
        parser.error("NVIDIA_API_KEY fehlt.")
    logging.basicConfig(level=logging.INFO, format="%(name)s %(message)s")
    assistant = Assistant(OllamaModel(args.model) if args.model else FixtureModel())
    try:
        if args.command == "ask":
            print(DISCLOSURE, flush=True)
            print(json.dumps(asdict(assistant.ask(args.question)), ensure_ascii=False, indent=2))
            return 0
        reports = [evaluate(assistant, args.runs)]
        for name in args.compare_model:
            reports.append(evaluate(Assistant(OllamaModel(name)), args.runs))
        if args.nvidia_model:
            for prompt in ("direct", "grounded"):
                model = NvidiaModel(args.nvidia_model, prompt, os.environ["NVIDIA_API_KEY"])
                reports.append(evaluate(Assistant(model), args.runs))
    except (OSError, ValueError, KeyError):
        parser.exit(2, "Anfrage abgebrochen: Modell nicht erreichbar oder Antwortformat ungültig.\n")
    for report in reports:
        print(f"Modell: {report['model']} | Fälle: {report['case_count']} | Wiederholungen: {report['runs']}")
        for row in report["totals"]:
            mode = "Guardrail" if row["guarded"] else "Baseline"
            print(f"{mode:10} {row['passed']}/{row['total']} | "
                  f"p95 {row['p95_ms']:.2f} ms | Fehler: {row['errors']} | auffällige Gebührenausgaben: {row['flagged_fee_outputs']}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(reports[0] if len(reports) == 1 else reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return int(any(row["guarded"] and not row["passed"] for report in reports for row in report["results"]))


if __name__ == "__main__":
    raise SystemExit(main())
