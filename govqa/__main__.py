import argparse
import hashlib
import json
import logging
import statistics
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from .assistant import DATA, DISCLOSURE, FALLBACK, Assistant
from .models import FixtureModel, OllamaModel


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
                start = time.perf_counter()
                answer = assistant.ask(case["question"], guarded=guarded)
                passed = (
                    answer.text == expected and answer.source == source and answer.topic == topic
                )
                row = dict(case_id=case["id"], group=case["group"], run=run, guarded=guarded,
                           passed=passed, latency_ms=round((time.perf_counter() - start) * 1000, 2),
                           answer=asdict(answer))
                rows.append(row)
                groups[case["group"], guarded].append(row)
    summary = [
        dict(group=group, guarded=guarded, passed=sum(row["passed"] for row in entries),
             total=len(entries), median_ms=statistics.median(row["latency_ms"] for row in entries))
        for (group, guarded), entries in groups.items()
    ]
    return {
        "model": assistant.model.name,
        "runs": runs,
        "case_count": len(cases),
        "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "documents_sha256": hashlib.sha256((DATA / "documents.json").read_bytes()).hexdigest(),
        "summary": summary,
        "results": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=DISCLOSURE)
    parser.add_argument("--model", help="Lokales Ollama-Modell. Standard: deterministische Fixture.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    ask = subcommands.add_parser("ask")
    ask.add_argument("question")
    evaluate_command = subcommands.add_parser("evaluate")
    evaluate_command.add_argument("--runs", type=int, default=1)
    evaluate_command.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "evaluate" and args.runs < 1:
        parser.error("--runs muss mindestens 1 sein.")
    logging.basicConfig(level=logging.INFO, format="%(name)s %(message)s")
    assistant = Assistant(OllamaModel(args.model) if args.model else FixtureModel())
    try:
        if args.command == "ask":
            print(DISCLOSURE, flush=True)
            print(json.dumps(asdict(assistant.ask(args.question)), ensure_ascii=False, indent=2))
            return 0
        report = evaluate(assistant, args.runs)
    except (OSError, ValueError, KeyError):
        parser.exit(2, "Anfrage abgebrochen: Modell nicht erreichbar oder Antwortformat ungültig.\n")
    print(f"Modell: {report['model']} | Fälle: {report['case_count']} | Wiederholungen: {report['runs']}")
    for row in report["summary"]:
        mode = "Guardrail" if row["guarded"] else "Baseline"
        print(f"{row['group']:12} {mode:10} {row['passed']:3}/{row['total']:<3} "
              f"Median {row['median_ms']:.2f} ms")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return int(any(row["guarded"] and not row["passed"] for row in report["results"]))


if __name__ == "__main__":
    raise SystemExit(main())
