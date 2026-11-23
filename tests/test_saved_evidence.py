"""Audit archived synthetic-case evidence; does not call a live model."""
import hashlib
import json
from pathlib import Path
import unittest

from govqa.report import comparison, paired_comparison

ROOT = Path(__file__).resolve().parents[1]


class SavedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.reports = json.loads((ROOT / "evidence/arena-nvidia-paced.json").read_text())

    def test_live_report_matches_current_test_data_and_totals(self):
        for report in self.reports:
            for field, path in [("cases_sha256", "cases.json"), ("documents_sha256", "documents.json")]:
                self.assertEqual(report[field], hashlib.sha256((ROOT / "data" / path).read_bytes()).hexdigest())
            for total in report["totals"]:
                rows = [row for row in report["results"] if row["guarded"] == total["guarded"]]
                self.assertEqual(len(rows), 50)
                self.assertEqual(sum(row["passed"] for row in rows), total["passed"])
                self.assertTrue(all(row["error"] is None for row in rows))

    def test_comparison_can_be_reconstructed_from_saved_evidence(self):
        expected = json.loads((ROOT / "evidence/arena-nvidia-paced-comparison.json").read_text())
        self.assertEqual(expected, {"variants": comparison(self.reports), "pairs": paired_comparison(self.reports)})

    def test_open_findings_match_all_remaining_grounded_failures(self):
        grounded = next(r for r in self.reports if r["model"].endswith(":grounded"))
        failed = {r["case_id"] for r in grounded["results"] if r["guarded"] and not r["passed"]}
        findings = json.loads((ROOT / "evidence/open-findings.json").read_text())
        self.assertEqual(failed, {"04", "08"})
        self.assertEqual({f["case_id"] for f in findings["findings"]}, failed)
        self.assertTrue(all(f["status"] == "open" for f in findings["findings"]))


if __name__ == "__main__":
    unittest.main()
