"""Compare arena reports and optionally estimate costs from supplied token rates."""

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path


def comparison(reports, input_rate=None, output_rate=None):
    if (input_rate is None) != (output_rate is None):
        raise ValueError("Provide both token rates.")
    fingerprints = {
        (report["cases_sha256"], report["documents_sha256"], report["runs"])
        for report in reports
    }
    if len(fingerprints) != 1:
        raise ValueError("Reports must use the same cases, facts and run count.")

    rows = []
    for report in reports:
        for total in report["totals"]:
            group = [row for row in report["results"] if row["guarded"] == total["guarded"]]
            failures = Counter(row["error"] for row in group if row.get("error") is not None)
            processed = len(group) - sum(failures.values())
            usage = total["usage_totals"]
            prompt_tokens = usage.get("prompt_eval_count")
            completion_tokens = usage.get("eval_count")
            estimate = None
            if (
                input_rate is not None and prompt_tokens is not None and completion_tokens is not None
                and not failures
            ):
                estimate = round((prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000, 6)
            rows.append({
                "variant": report["model"],
                "guarded": total["guarded"],
                "passed": total["passed"],
                "total": total["total"],
                "flagged_fee_outputs": total["flagged_fee_outputs"],
                "errors": sum(failures.values()),
                "errors_by_type": dict(failures),
                "processed": processed,
                "pass_rate_all_cases": total["passed"] / len(group) if group else None,
                "pass_rate_processed_cases": total["passed"] / processed if processed else None,
                "p95_ms": total["p95_ms"],
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "estimated_eur_from_reported_tokens": estimate,
            })
    return rows


def paired_comparison(reports):
    """Compare prompts only on the same technically completed case/run pairs."""
    pairs = []
    for left, right in combinations(reports, 2):
        if left["model"] == "fixture" or right["model"] == "fixture":
            continue
        for guarded in (False, True):
            def outcomes(report):
                return {
                    (row["case_id"], row["run"]): row
                    for row in report["results"] if row["guarded"] == guarded
                }

            a, b = outcomes(left), outcomes(right)
            if a.keys() != b.keys():
                raise ValueError("Reports have different case/run pairs.")
            complete = [key for key in a if a[key].get("error") is None and b[key].get("error") is None]
            pairs.append({
                "left": left["model"], "right": right["model"], "guarded": guarded,
                "total_pairs": len(a), "processed_by_both": len(complete),
                "both_passed": sum(a[key]["passed"] and b[key]["passed"] for key in complete),
                "left_only_passed": sum(a[key]["passed"] and not b[key]["passed"] for key in complete),
                "right_only_passed": sum(b[key]["passed"] and not a[key]["passed"] for key in complete),
                "neither_passed": sum(not a[key]["passed"] and not b[key]["passed"] for key in complete),
            })
    return pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--paired", action="store_true")
    parser.add_argument("--input-eur-per-million", type=float)
    parser.add_argument("--output-eur-per-million", type=float)
    args = parser.parse_args()
    rates = (args.input_eur_per_million, args.output_eur_per_million)
    if any(rate is not None and not 0 <= rate < float("inf") for rate in rates):
        parser.error("Token rates must be finite and non-negative.")
    report = json.loads(args.report.read_text(encoding="utf-8"))
    reports = report if isinstance(report, list) else [report]
    try:
        rows = comparison(reports, *rates)
        result = {"variants": rows, "pairs": paired_comparison(reports)} if args.paired else rows
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
