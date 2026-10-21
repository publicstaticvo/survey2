"""CLI integration tests for historical evidence and ProReviewer compatibility."""
import json
from pathlib import Path
import subprocess
import sys
import shutil
import uuid
import unittest

import pymupdf

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "review_cli.py"


class ReviewCLI(unittest.TestCase):
    def setUp(self):
        # Python 3.14's Windows mode=0700 tempfile directory ACL is incompatible
        # with some sandbox tokens; use an ordinary workspace directory instead.
        test_parent = Path(__file__).resolve().parent
        self.root = test_parent / ("_tmp_" + uuid.uuid4().hex)
        self.root.mkdir()
        assert self.root.resolve().parent == test_parent
        self.addCleanup(shutil.rmtree, self.root)
        self.run_dir = self.root / "review"
        self.paper = self.root / "survey.pdf"
        with pymupdf.open() as doc:
            page = doc.new_page()
            page.insert_text((72, 72), "Survey of Methods\nWe distinguish two method families.\nPublished 14 March 2025.")
            doc.save(self.paper)

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                encoding="utf-8", capture_output=True, cwd=self.root)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def initialize(self, date=True):
        args = ["init", self.paper, "--dir", self.run_dir]
        if date:
            args += ["--publication-date", "2025-03-14", "--date-basis", "User specified"]
        self.cli(*args)

    def command(self, *args, **kwargs):
        return self.cli("--dir", self.run_dir, *args, **kwargs)

    def data(self, command, data, *args, ok=True):
        path = self.root / "payload.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return self.command(command, *args, "--file", path, ok=ok)

    def put(self, kind, data, ok=True):
        return self.data("put", data, kind, ok=ok)

    def evidence(self):
        return {"kind": "external", "title": "Earlier study", "url": "https://example.org/v1.pdf",
                "version": "v1", "available_date": "2025-03-14", "date_basis": "Version history",
                "location": "p. 2", "excerpt": "Two families have different assumptions.",
                "purpose": "Check synthesis", "status": "verified"}

    def test_roundtrip_and_full_review(self):
        self.initialize()
        self.assertIn("<!-- page 1 -->", (self.run_dir / "paper.md").read_text(encoding="utf-8"))
        self.command("add_claim", "--text", "中文综合认识", "--section", "§1", "--claim_type", "synthesis")
        self.command("update_claim", "--id", "C1", "--status", "supported", "--reason", "Verified against source", "--cross_refs", "§2")
        self.command("add_question", "--text", "Boundary?", "--section", "§1", "--related_claims", "C1")
        self.command("resolve_question", "--id", "Q1", "--answer", "Boundary explained", "--sections", "§2")
        self.command("add_note", "--text", "Useful distinction", "--section", "§1")
        self.put("search", {"query": "method families", "query_target": "Verify synthesis", "tool": "web", "status": "success"})
        self.put("evidence", {"kind": "paper", "location": "p. 1", "excerpt": "We distinguish two method families.", "purpose": "Synthesis", "status": "verified"})
        self.put("evidence", self.evidence())
        self.put("contribution", {"statement": "Clarifies method assumptions", "paper_locations": ["p. 1"], "evidence_ids": ["E1", "E2"]})
        self.put("contribution", {"id": "K1", "correctness_status": "supported", "reason": "Source confirms distinction"})
        self.data("point", {"text": "Useful evidence-grounded distinction", "evidence_refs": ["K1"]}, "--section", "strengths")
        self.data("point", {"text": "Helpful organization", "evidence_refs": ["N1"]}, "--section", "comments")
        self.command("outline", "--section", "summary", "--content", "Survey compares methods")
        self.command("outline", "--section", "overall_score", "--content", "6")
        self.data("judgment", {"reason": "Reliable central distinction outweighs auxiliary limitations", "refs": ["K1", "C1"], "limitations": "Limited search"})
        self.command("step", "--target", "K1", "--why", "Central", "--action", "Read sources", "--found", "Supported distinction")
        self.command("audit")
        self.command("finalize")
        review = (self.run_dir / "review.md").read_text(encoding="utf-8")
        self.assertIn("[K1](#k1)", review)
        self.assertIn('id="c1"', review)
        self.assertIn('id="n1"', review)
        self.assertIn("2025-03-14", review)
        self.assertTrue((self.run_dir / "steps.md").exists())
        state = json.loads((self.run_dir / "review_log.json").read_text(encoding="utf-8"))
        self.assertEqual(state["contributions"][0]["correctness_status"], "supported")
        self.assertEqual(state["review_outline"]["strengths"][0]["evidence_refs"], ["K1"])
        self.command("show", "--detailed")
        self.command("export", "--no-evidence")
        plain_review = (self.run_dir / "review.md").read_text(encoding="utf-8")
        self.assertNotIn("](#", plain_review)

    def test_date_and_version_gate(self):
        self.initialize(False)
        self.assertIn("Confirm publication_date", self.command("audit", ok=False).stdout)
        self.put("evidence", self.evidence(), ok=False)
        self.data("context", {"publication_date": "2025-03-14", "date_basis": "Verified publisher record", "version": "v1"})
        self.put("evidence", self.evidence())
        self.put("evidence", self.evidence() | {"available_date": "2025-03-15"}, ok=False)
        self.put("evidence", self.evidence() | {"version": ""}, ok=False)
        self.put("evidence", self.evidence() | {"date_basis": ""}, ok=False)
        self.data("context", {"publication_date": "2025-03-13"}, ok=False)

    def test_provisional_evidence_not_decisive(self):
        self.initialize()
        self.put("evidence", self.evidence() | {"available_date": "2026-01-01", "status": "excluded"})
        self.put("contribution", {"statement": "Synthesis", "paper_locations": ["p. 1"], "evidence_ids": ["E1"]})
        self.data("judgment", {"reason": "Conclusion", "refs": ["K1"], "limitations": "No score"})
        self.command("outline", "--section", "summary", "--content", "Summary")
        result = self.command("finalize", ok=False)
        self.assertIn("ineligible external evidence", result.stderr)
        self.assertFalse((self.run_dir / "review.md").exists())
        self.command("export", ok=False)

    def test_locations_missing_ids_and_input_integrity(self):
        self.initialize()
        self.put("evidence", {"kind": "paper", "location": "p. 9", "excerpt": "We distinguish two method families.", "purpose": "Check", "status": "verified"}, ok=False)
        self.put("evidence", {"kind": "paper", "location": "p. 1", "excerpt": "Invented text", "purpose": "Check", "status": "verified"}, ok=False)
        self.data("point", {"text": "Missing evidence", "evidence_refs": ["K99"]}, "--section", "weaknesses", ok=False)
        self.put("expectation", {"expectation": "Compare assumptions", "origins": ["Z"], "basis_evidence_ids": [], "scope": "Core"}, ok=False)
        (self.run_dir / "paper.md").write_text("Changed manuscript", encoding="utf-8")
        self.assertIn("changed since initialization", self.command("audit", ok=False).stdout)

    def test_expectation_and_conference_score(self):
        self.initialize()
        self.put("expectation", {"expectation": "Explain comparison", "origins": ["A"], "basis_evidence_ids": [], "scope": "Promised comparison"})
        self.data("judgment", {"reason": "Decisive missing synthesis", "refs": ["X1"], "limitations": "No score"})
        self.command("outline", "--section", "summary", "--content", "Summary")
        self.assertIn("exploratory expectation", self.command("audit", ok=False).stdout)
        self.command("outline", "--section", "overall_score", "--content", "7", ok=False)
        self.command("set_conference", "acl")
        self.command("outline", "--section", "overall_score", "--content", "3.5")


if __name__ == "__main__":
    unittest.main()
