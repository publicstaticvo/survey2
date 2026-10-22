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
        self.run_dir = self.root / "review_survey"
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

    def discovery(self):
        self.put("discovery", {"route": "manuscript", "disposition": "no_candidate", "reason": "Read all sections; no additional necessary synthesis found"})
        self.put("discovery", {"route": "field", "disposition": "limited", "reason": "Search limited to the comparison sources; no independent topic investigation", "uncertainty": "External discovery incomplete"})

    def inference_audit(self, **changes):
        return {"target": "K1", "inference": "Source assumptions support the two-family distinction",
                "evidence_ids": ["E1"], "author_response": "Scope is explicitly limited to two families",
                "investigation": "Read paper p. 1 and source comparison", "verdict": "supported",
                "reason": "Distinction follows at the stated scope", **changes}

    def impact(self, **changes):
        return {"finding": "Reliable distinction supports a useful entry point", "target_refs": ["K1"],
                "evidence_refs": ["A1"], "direction": "supports", "extent": "main",
                "reason": "Readers can distinguish the two assumption sets", "status": "established", **changes}

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
        self.put("contribution", {"id": "K1", "correctness_status": "supported", "reason": "Source confirms distinction",
                                  "correctness_reason": "Source confirms scope", "increment_reason": "Useful reorganization; search limited",
                                  "significance_reason": "Helps select an assumption family"})
        self.discovery()
        self.put("audit", self.inference_audit())
        self.put("impact", self.impact())
        self.data("point", {"text": "Useful evidence-grounded distinction", "evidence_refs": ["K1"]}, "--section", "strengths")
        self.data("point", {"text": "Helpful organization", "evidence_refs": ["N1"]}, "--section", "comments")
        self.command("outline", "--section", "summary", "--content", "Survey compares methods")
        self.command("outline", "--section", "overall_score", "--content", "6")
        self.data("judgment", {"reason": "Reliable central distinction outweighs auxiliary limitations", "refs": ["I1", "C1"], "limitations": "Limited search",
                               "scale_reason": "A useful synthesis merits 6, while limited comparative depth prevents 8; more useful than the weak category"})
        self.command("step", "--target", "K1", "--why", "Central", "--action", "Read sources", "--found", "Supported distinction")
        self.command("audit")
        self.command("finalize")
        review = (self.run_dir / "review.md").read_text(encoding="utf-8")
        self.assertIn("[K1](#k1)", review)
        self.assertIn('id="c1"', review)
        self.assertIn('id="n1"', review)
        self.assertIn('id="a1"', review)
        self.assertIn('id="i1"', review)
        self.assertIn("Expectation discovery and screening", (self.run_dir / "audit_summary.md").read_text(encoding="utf-8"))
        self.assertIn("2025-03-14", review)
        self.assertTrue((self.run_dir / "steps.md").exists())
        state = json.loads((self.run_dir / "review_log.json").read_text(encoding="utf-8"))
        self.assertEqual(state["contributions"][0]["correctness_status"], "supported")
        self.assertEqual(state["review_outline"]["strengths"][0]["evidence_refs"], ["K1"])
        self.command("show", "--detailed")
        self.command("export", "--no-evidence")
        plain_review = (self.run_dir / "review.md").read_text(encoding="utf-8")
        self.assertNotIn("](#", plain_review)
        self.command("export", "--output", "alternate.md", ok=False)
        self.assertFalse((self.run_dir / "alternate.md").exists())

    def test_naming_and_collision_guards(self):
        self.cli("init", self.paper, "--dir", self.root / "arbitrary", ok=False)
        self.assertFalse((self.root / "arbitrary").exists())
        self.cli("init", self.paper)
        self.assertTrue((self.run_dir / "input_manifest.json").exists())
        original = (self.run_dir / "review_log.json").read_bytes()
        self.cli("init", self.paper, ok=False)
        self.cli("init", self.paper, "--force", ok=False)
        self.assertEqual(original, (self.run_dir / "review_log.json").read_bytes())
        name = "Survey title with spaces " + "long" * 16 + ".md"
        long_paper = self.root / name
        long_paper.write_text("A survey", encoding="utf-8")
        self.cli("init", long_paper)
        self.assertTrue((self.root / ("review_" + long_paper.stem) / "paper.md").exists())

    def test_exact_duplicates_rejected_without_mutation(self):
        self.initialize()
        self.put("contribution", {"statement": "A useful synthesis", "paper_locations": ["p. 1"]})
        before = (self.run_dir / "review_log.json").read_bytes()
        result = self.put("contribution", {"statement": "  A USEFUL   synthesis ", "paper_locations": ["p. 1"]}, ok=False)
        self.assertIn("Exact duplicate of K1", result.stderr)
        self.assertEqual(before, (self.run_dir / "review_log.json").read_bytes())
        self.put("expectation", {"expectation": "Compare assumptions", "origins": ["A"], "basis_evidence_ids": [], "scope": "Core"})
        self.put("expectation", {"expectation": "Compare assumptions", "origins": ["B"], "basis_evidence_ids": [], "scope": "Core"}, ok=False)
        self.put("contribution", {"id": "K1", "reason": "Updated in place"})

    def test_v2_decision_guards_and_legacy_reading(self):
        self.initialize()
        self.put("contribution", {"statement": "Synthesis", "paper_locations": ["p. 1"]})
        self.put("audit", self.inference_audit(challenge="Alternative explanation", challenge_basis=""), ok=False)
        self.put("impact", self.impact(evidence_refs=["K1"], status="uncertain"))
        self.data("judgment", {"reason": "Unresolved", "refs": ["I1"], "limitations": "Incomplete"})
        self.command("outline", "--section", "summary", "--content", "Summary")
        self.command("outline", "--section", "overall_score", "--content", "6")
        errors = self.command("audit", ok=False).stdout
        self.assertIn("unresolved impact", errors)
        self.assertIn("Record field discovery", errors)
        self.assertIn("separate correctness", errors)
        state_path = self.run_dir / "review_log.json"
        old = json.loads(state_path.read_text(encoding="utf-8"))
        for key in ("schema_version", "discoveries", "audits", "impacts", "scale_reason"):
            old.pop(key, None)
        old["overall_refs"] = ["K1"]
        state_path.write_text(json.dumps(old), encoding="utf-8")
        self.command("show")
        self.assertNotIn("Record field discovery", self.command("audit", ok=False).stdout)

    def test_new_references_cannot_hide_post_cutoff_evidence(self):
        self.initialize()
        self.put("evidence", self.evidence() | {"available_date": "2026-01-01", "status": "excluded"})
        self.discovery()
        self.put("impact", self.impact(target_refs=[], independent_quality="Trustworthiness", evidence_refs=["E1"]))
        self.data("judgment", {"reason": "Finding", "refs": ["I1"], "limitations": "No score"})
        self.command("outline", "--section", "summary", "--content", "Summary")
        self.assertIn("ineligible external evidence", self.command("audit", ok=False).stdout)
        self.put("audit", self.inference_audit(target="K99"), ok=False)

    def test_no_score_can_report_inability_to_judge(self):
        self.initialize()
        self.discovery()
        self.command("add_note", "--text", "Source unavailable", "--section", "All sections checked")
        self.put("impact", self.impact(target_refs=[], scholarly_use="Comparative guidance", evidence_refs=["N1"],
                                       direction="unknown", extent="unknown", status="uncertain", reason="Access prevents verification"))
        self.data("judgment", {"reason": "Cannot judge overall quality given missing central evidence", "refs": ["I1"], "limitations": "Source access failed"})
        self.command("outline", "--section", "summary", "--content", "Survey scope reviewed; overall judgment unresolved")
        self.command("finalize")
        self.assertTrue((self.run_dir / "audit_summary.md").exists())

    def test_expected_contribution_discovery_and_absence_checks(self):
        self.initialize()
        self.put("evidence", {"kind": "paper", "location": "p. 1", "excerpt": "We distinguish two method families.", "purpose": "Scope", "status": "verified"})
        self.put("evidence", self.evidence())
        self.put("discovery", {"route": "manuscript", "disposition": "no_candidate", "reason": "No unfulfilled promises found"})
        self.put("discovery", {"route": "field", "disposition": "candidate", "question": "Which assumptions support each choice?",
                               "basis_evidence_ids": ["E2"], "scope_and_use": "Supports the survey's method choice goal",
                               "possible_synthesis": "Compare assumption sets", "reason": "Source exposes a consequential distinction"})
        self.put("expectation", {"expectation": "Compare assumptions", "origins": ["C", "D"], "basis_evidence_ids": ["E2"],
                                 "discovery_ids": ["D2"], "scope": "Comparative goal", "tier": "decision_relevant",
                                 "independence_reason": "External source supplies grounds independent of the reviewer preference",
                                 "missing_status": "confirmed", "checked_locations": []})
        self.put("impact", self.impact(target_refs=["X1"], evidence_refs=["E1", "E2"], direction="weakens"))
        self.data("judgment", {"reason": "Conditional guidance is materially incomplete", "refs": ["I1"], "scale_reason": "6 is justified by remaining utility; broader support needed for 8"})
        self.command("outline", "--section", "summary", "--content", "Survey comparison")
        self.command("outline", "--section", "overall_score", "--content", "6")
        self.assertIn("confirmed absence needs checked_locations", self.command("audit", ok=False).stdout)
        self.put("expectation", {"id": "X1", "checked_locations": ["All text, tables and appendices"]})
        self.command("finalize")
        review = (self.run_dir / "review.md").read_text(encoding="utf-8")
        self.assertIn('id="d2"', review)
        self.assertIn('id="x1"', review)

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
        self.command("outline", "--section", "overall_score", "--content", "6")
        self.assertIn("exploratory expectation", self.command("audit", ok=False).stdout)
        self.command("outline", "--section", "overall_score", "--content", "7", ok=False)
        self.command("set_conference", "acl")
        self.command("outline", "--section", "overall_score", "--content", "3.5")


if __name__ == "__main__":
    unittest.main()
