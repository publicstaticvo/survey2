import json
import subprocess
import sys
import unittest
import uuid
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
CLI = SKILL_DIR / "scripts" / "review_cli.py"
PAPER = (
    SKILL_DIR.parents[2]
    / "golden"
    / "review_pdfs"
    / "human_testset"
    / "001_grounding_and_validation_of_algorithmic_recourse_in_real_world_contexts_a_systematized_lit_oEmyoy5H5P.pdf"
)


class ReviewCliIntegrationTest(unittest.TestCase):
    def run_cli(self, *args, expected=0):
        result = subprocess.run(
            [sys.executable, str(CLI), *map(str, args)],
            cwd=SKILL_DIR,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            expected,
            msg=f"command failed: {args}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def write_payload(self, directory, name, payload):
        path = directory / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_records_update_validation_and_safe_finalize(self):
        self.assertTrue(PAPER.is_file())
        parent = SKILL_DIR / "tests" / "_tmp_v3"
        parent.mkdir(exist_ok=True)
        token = uuid.uuid4().hex
        input_copy = parent / f"cli_test_{token}.pdf"
        input_copy.write_bytes(PAPER.read_bytes())
        init = self.run_cli(
            "init", input_copy, "--output-parent", parent,
            "--conference", "iclr",
        )
        run = Path(init.stdout.strip())
        expected_name = "review_" + input_copy.stem
        self.assertEqual(run.name, expected_name)
        self.assertTrue((run / "paper.md").is_file())

        state_path = run / "review_log.json"
        original_state = state_path.read_bytes()
        self.run_cli("init", input_copy, "--output-parent", parent, expected=1)
        self.assertEqual(state_path.read_bytes(), original_state)

        manuscript_text = (run / "paper.md").read_text(encoding="utf-8")
        excerpt = "We find that there is a strong disconnect"
        self.assertIn(excerpt, manuscript_text)

        knowledge = self.write_payload(parent, f"knowledge_{token}.json", {
                "statement": "The reviewed AR literature is disconnected from practical requirements, while real-world grounding and validation remain underexplored.",
                "scope": "The 127 publications reviewed in this manuscript.",
                "paper_locations": ["PDF p. 1, Abstract, lines 17-20"],
                "result_form": "synthesis",
                "knowledge_relation": "review_synthesis",
                "extraction_reason": "The abstract states a field-level diagnosis across the reviewed publications.",
            })
        self.run_cli("--dir", run, "add_knowledge", "--file", knowledge)

        evidence = self.write_payload(parent, f"evidence_{token}.json", {
                "source_type": "manuscript",
                "source_identity": PAPER.name,
                "version_date": "NeurIPS 2024 submitted manuscript; exact upload date not established",
                "location": "PDF p. 1, Abstract, lines 17-20",
                "excerpt": excerpt,
                "role": "support",
                "evaluation_role": "increment",
                "target_refs": ["K1"],
                "accessed_at": "2026-10-28T15:16:10Z",
                "cutoff_eligible": "unknown",
            })
        self.run_cli("--dir", run, "add_evidence", "--file", evidence)

        recommendation_excerpt = "We distill our findings into five key recommendations."
        self.assertIn(recommendation_excerpt, manuscript_text)
        recommendation_evidence = self.write_payload(parent, f"recommendation_evidence_{token}.json", {
            "source_type": "manuscript",
            "source_identity": input_copy.name,
            "version_date": "NeurIPS 2024 submitted manuscript; exact upload date not established",
            "location": "PDF p. 8, Section 5.1, lines 352-354",
            "excerpt": recommendation_excerpt,
            "role": "support",
            "evaluation_role": "expectation",
            "target_refs": ["X1"],
            "accessed_at": "2026-10-28T15:16:10Z",
            "cutoff_eligible": "unknown",
        })

        search = self.write_payload(parent, f"search_{token}.json", {
                "target_question": "Locate the submitted survey and a candidate source for later comparative investigation.",
                "query": "\"Grounding and validation of algorithmic recourse in real-world contexts\"",
                "tool": "web search",
                "status": "success",
                "result_urls": ["https://openreview.net/pdf?id=oEmyoy5H5P"],
                "checked_source_refs": [],
                "searched_at": "2026-10-28T15:16:10Z",
            })
        self.run_cli("--dir", run, "record_search", "--file", search)

        expectation = self.write_payload(parent, f"expectation_{token}.json", {
                "expectation": "Explain how the five recommendations follow from the identified practical gap.",
                "route": "ordinary_reader",
                "trigger_locations": ["PDF p. 1, Abstract, lines 17-21"],
                "trigger_reason": "The abstract promises five recommendations intended to improve adaptation to real-world applications.",
                "scope": "The recommendations presented by this survey.",
                "scholarly_use": "Connects the diagnosis to actionable guidance for readers.",
                "rationale": "This follows from the manuscript's explicit promise; full-paper presence remains unchecked.",
                "feasible_response": "The abstract and recommendation sections can be compared in the manuscript.",
            })
        self.run_cli("--dir", run, "add_expectation", "--file", expectation)
        self.run_cli("--dir", run, "add_evidence", "--file", recommendation_evidence)
        expectation_patch = self.write_payload(parent, f"expectation_patch_{token}.json", {
                "scholarly_use": "Helps readers connect the field-level diagnosis to the proposed guidance.",
            })
        self.run_cli("--dir", run, "update_expectation", "--id", "X1", "--file", expectation_patch)
        for dimension, status, reason in (
            ("rationality", "confirmed", "The abstract promises five recommendations and Section 5.1 explicitly maps them to findings from earlier sections."),
            ("presence", "present", "Section 5.1 states the five recommendations and identifies the findings that motivate them."),
        ):
            payload = self.write_payload(parent, f"expectation_assessment_{dimension}_{token}.json", {
                "target_id": "X1",
                "dimension": dimension,
                "question": f"Is the expected result {dimension}?",
                "status": status,
                "reason": reason,
                "evidence_refs": ["E2"],
                "counter_evidence_refs": [],
                "unresolved": "",
                "cutoff": "The submitted manuscript version; exact upload date not established",
            })
            self.run_cli("--dir", run, "assess", "--file", payload)

        knowledge_patch = self.write_payload(parent, f"knowledge_patch_{token}.json", {
                "extraction_reason": "The abstract states a bounded diagnosis about the 127 reviewed publications and separately promises five recommendations.",
            })
        self.run_cli("--dir", run, "update_knowledge", "--id", "K1", "--file", knowledge_patch)

        assessments = [
            ("increment_identification", "possible_increment", "The abstract expresses a separately checkable review-level diagnosis.", ""),
            ("correctness", "unknown", "The manuscript states the diagnosis; checking the underlying 127 publications was outside this CLI integration test.", "The source population and coding were not independently audited."),
            ("novelty", "unknown", "The title search located this manuscript, but no prior-survey comparison was performed.", "A comparative search and inspection of closest prior surveys remain necessary."),
            ("value", "unknown", "The abstract connects the diagnosis to practical adaptation; the usefulness of that guidance has not been evaluated here.", "The recommendation-to-use relation has not been assessed."),
        ]
        for dimension, status, reason, unresolved in assessments:
            payload = self.write_payload(parent, f"assessment_{dimension}_{token}.json", {
                    "target_id": "K1",
                    "dimension": dimension,
                    "question": f"Does the candidate satisfy {dimension}?",
                    "status": status,
                    "reason": reason,
                    "evidence_refs": ["E1"],
                    "counter_evidence_refs": [],
                    "unresolved": unresolved,
                    "cutoff": "Not established in this integration test",
                })
            self.run_cli("--dir", run, "assess", "--file", payload)

        impact = self.write_payload(parent, f"impact_{token}.json", {
                "finding": "The abstract advances a central diagnosis but its evidential support and reader impact remain unverified in this run.",
                "target_refs": ["K1"],
                "evidence_refs": ["E1"],
                "direction": "qualifies",
                "extent": "main",
                "effect": "The diagnosis may shape how readers interpret the survey's practical recommendations.",
                "reason": "The abstract links a field-level diagnosis to five recommendations; the evidence and use implications need further review.",
                "status": "uncertain",
                "uncertainty": "The full supporting analysis and recommendation mapping have not been reviewed.",
            })
        self.run_cli("--dir", run, "add_impact", "--file", impact)
        impact_patch = self.write_payload(parent, f"impact_patch_{token}.json", {
                "uncertainty": "The source analysis and recommendation mapping remain unchecked.",
            })
        self.run_cli("--dir", run, "update_impact", "--id", "I1", "--file", impact_patch)

        self.run_cli(
            "--dir", run, "step",
            "--target", "K1",
            "--why", "Initial inspection of the abstract",
            "--action", "Read the abstract in the supplied PDF-derived text",
            "--found", "Recorded the field-level diagnosis as a candidate; broader validation remains open",
            "--ops", "add_knowledge K1; add_evidence E1; add_expectation X1",
        )
        summary = self.write_payload(parent, f"point_{token}.json", {
                "text": "The abstract presents a field-level diagnosis and ties it to practical recommendations.",
                "evidence_refs": ["E1"],
            })
        self.run_cli("--dir", run, "point", "--section", "comments", "--file", summary)
        self.run_cli("--dir", run, "outline", "--section", "summary", "--content", "The abstract proposes a practical diagnosis and five recommendations; full assessment is incomplete.")
        judgment = self.write_payload(parent, f"judgment_{token}.json", {
                "reason": "This integration fixture exercises export mechanics and does not provide a scholarly quality judgment.",
                "refs": ["K1", "X1", "I1"],
                "limitations": "The fixture uses a narrow set of actual manuscript passages and is not a completed review.",
            })
        self.run_cli("--dir", run, "judgment", "--file", judgment)
        self.run_cli("--dir", run, "show", "--detailed")
        self.run_cli("--dir", run, "validate")
        self.run_cli("--dir", run, "finalize")
        self.assertTrue((run / "review.md").is_file())

        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["schema_version"], 3)
        self.assertEqual(state["knowledge_units"][0]["data"]["increment_identification_status"], "possible_increment")
        self.assertEqual(len(state["knowledge_units"][0]["data"]["revision_history"]), 1)
        self.assertEqual(len(state["expectations"][0]["data"]["revision_history"]), 1)
        self.assertEqual(len(state["impacts"][0]["data"]["revision_history"]), 1)


if __name__ == "__main__":
    unittest.main()
