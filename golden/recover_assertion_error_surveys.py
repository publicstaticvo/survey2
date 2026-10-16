"""Recover survey candidates rejected only by the old evidence-quote assertion.

The decisions below were made manually from each submission's title and abstract.
Only accepted surveys are fetched again from OpenReview, and their PDFs are
downloaded exclusively from the PDF URL carried by the OpenReview submission.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import collect_openreview_survey_reviews_expanded as crawler
from golden.download_review_pdfs import (
    fetch_pdf,
    load_credentials,
    openreview_token,
    validate_source_url,
    write_pdf_atomic,
)


MANUAL_DECISIONS = {
    "5JIQE6HcTd": (False, "Method paper: it reviews dispersion methods but primarily proposes and evaluates new regularizers."),
    "kgrslrMVr1": (False, "Benchmark analysis paper evaluating whether time-series benchmarks measure the intended capabilities."),
    "bRVJcc89Em": (False, "Method and dataset paper introducing uncertainty quantification for generative video models."),
    "cZi9UlIu4K": (False, "Continual segmentation benchmark and method paper, not a literature synthesis."),
    "yEf8NSqTPu": (False, "Dataset paper describing collection and baselines for isolated ASL recognition."),
    "ISZPRsh5YV": (False, "Method and dataset paper for fine-grained video motion understanding."),
    "8V2Qf6mNx3": (False, "Evaluation benchmark paper for text-to-audio-video generation."),
    "08KOxSjRyj": (False, "Benchmark and method paper for long-context emotional intelligence."),
    "Xobl2VHyVb": (False, "Hardware design and verification benchmark paper."),
    "pMBsQ9ierF": (True, "Survey whose primary contribution is a holistic synthesis of emotional intelligence in intelligent agents."),
    "sSAp8ITBpC": (True, "Systematization-of-knowledge paper synthesizing red-teaming attacks, defenses, and practitioner strategies."),
    "04DbUMZGMD": (False, "Dataset and model paper for multimodal fact-checking."),
    "klzOWiyYn6": (False, "Method paper proposing a taxonomy, synthetic data process, and reward models."),
    "il6P7EHU1w": (False, "Visual-language moral alignment benchmark paper."),
    "8wEQLCSfCT": (False, "Geometric program reasoning benchmark paper."),
    "O06z2G18me": (False, "Empirical questionnaire-style survey administered to LLMs, not a literature survey."),
    "q36rpGlG9X": (False, "Empirical evaluation of LLM biomedical hypothesis generation."),
    "3PSApLjKex": (False, "Automated paper-writing framework and benchmark paper."),
}

MANUAL_VERSION = "manual-title-abstract-2026-10-02"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recover manually reviewed OpenReview surveys starting at record 297.")
    parser.add_argument("--start-index", type=int, default=297)
    parser.add_argument("--request-interval", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument(
        "--credentials-file",
        type=Path,
        default=Path(__file__).resolve().parent / "parse_golden_paper_content.py",
    )
    parser.add_argument(
        "--pdf-output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "review_pdfs" / "development_set",
    )
    parser.add_argument(
        "--audit-path",
        type=Path,
        default=Path(__file__).resolve().parent / ".openreview_state" / "manual_assertion_error_audit_2026-10-02.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state = crawler.read_json(crawler.STATE_PATH, {})
    candidates = state.get("candidates") or {}
    missing = sorted(set(MANUAL_DECISIONS) - set(candidates))
    if missing:
        raise RuntimeError(f"Candidates missing from crawler state: {missing}")

    audit_rows = []
    for forum, (is_survey, rationale) in MANUAL_DECISIONS.items():
        candidate = candidates[forum]
        title = str(candidate.get("title") or "").strip()
        abstract = str(candidate.get("abstract") or "").strip()
        if not title or not abstract:
            raise RuntimeError(f"{forum}: title or abstract is unavailable")
        audit_rows.append(
            {
                "openreview_forum_id": forum,
                "title": title,
                "abstract": abstract,
                "is_survey": is_survey,
                "rationale": rationale,
                "decision_source": MANUAL_VERSION,
            }
        )
    crawler.write_json(args.audit_path, audit_rows)

    existing_forums, existing_titles, _, _ = crawler.load_existing()
    accepted_forums = [forum for forum, decision in MANUAL_DECISIONS.items() if decision[0]]
    accepted_not_written = [forum for forum in accepted_forums if forum not in existing_forums]
    expected_indices = {
        forum: args.start_index + offset
        for offset, forum in enumerate(accepted_forums)
    }
    for forum in accepted_not_written:
        expected_index = expected_indices[forum]
        collisions = list(crawler.OUT_DIR.glob(f"{expected_index:03d}_*.json"))
        if collisions:
            raise RuntimeError(
                f"Record index {expected_index} is already occupied by {collisions[0].name}"
            )

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    token = openreview_token(
        opener,
        load_credentials(args.credentials_file),
        args.timeout,
        args.retries,
    )
    crawler.OPENREVIEW_TOKEN = token
    crawler.REQUEST_INTERVAL = max(0.0, args.request_interval)

    accepted = []
    staging_dir = crawler.STATE_DIR / "manual_assertion_recovery_pdfs"
    for forum in accepted_not_written:
        record = crawler.build_record(candidates[forum], 2, 1800, 1, 600)
        if record is None:
            raise RuntimeError(f"{forum}: submission or qualifying public reviews are unavailable")
        decision = {
            "is_survey": True,
            "confidence": "high",
            "rationale": MANUAL_DECISIONS[forum][1],
            "evidence_quote": str(candidates[forum]["title"]),
            "detector_version": MANUAL_VERSION,
        }
        record["llm_survey_decision"] = decision
        source_url = str(record.get("paper_url") or "").strip()
        validate_source_url(source_url, forum)
        data = fetch_pdf(source_url, token, args.timeout, args.retries)
        staged_pdf = staging_dir / f"{forum}.pdf"
        write_pdf_atomic(staged_pdf, data)
        accepted.append(
            {
                "forum": forum,
                "status": "accepted",
                "record": record,
                "staged_pdf": str(staged_pdf),
                "llm_decision": decision,
                "expected_index": expected_indices[forum],
            }
        )

    written = []
    for item in accepted:
        expected_index = item["expected_index"]
        new_rows = crawler.append_records(
            [item],
            existing_forums,
            existing_titles,
            expected_index - 1,
            args.pdf_output_dir,
        )
        if len(new_rows) != 1 or not new_rows[0]["file"].startswith(f"{expected_index:03d}_"):
            raise RuntimeError(f"Failed to materialize {item['forum']} as record {expected_index}")
        written.extend(new_rows)

    state = crawler.read_json(crawler.STATE_PATH, {})
    state.setdefault("forum_status", {})
    state.setdefault("llm_decisions", {})
    state.setdefault("errors", {})
    written_forums = {
        json.loads((crawler.OUT_DIR / row["file"]).read_text(encoding="utf-8"))["openreview_forum_id"]
        for row in written
    }
    for forum, (is_survey, rationale) in MANUAL_DECISIONS.items():
        decision = {
            "is_survey": is_survey,
            "confidence": "high",
            "rationale": rationale,
            "evidence_quote": str(candidates[forum]["title"]),
            "detector_version": MANUAL_VERSION,
        }
        state["llm_decisions"][forum] = decision
        state["forum_status"][forum] = "written" if forum in written_forums or forum in existing_forums else "llm-not-survey"
        state["errors"].pop(f"forum::{forum}", None)
    crawler.write_json(crawler.STATE_PATH, state)

    for path in crawler.OUT_DIR.glob("*.json"):
        if path.name.startswith("_"):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        forum = payload.get("openreview_forum_id")
        if forum not in accepted_forums:
            continue
        payload["llm_survey_decision"] = state["llm_decisions"][forum]
        crawler.write_json(path, payload)

    extra_rows = crawler.read_json(crawler.EXTRA_INDEX_PATH, [])
    rows_by_file = {
        row["file"]: row
        for row in extra_rows
        if isinstance(row, dict) and row.get("file")
    }
    for row in written:
        rows_by_file[row["file"]] = row
    crawler.rebuild_indexes(list(rows_by_file.values()))

    summary = crawler.read_json(crawler.SUMMARY_PATH, {})
    summary_errors = summary.get("errors") or {}
    for forum in MANUAL_DECISIONS:
        summary_errors.pop(forum, None)
        summary_errors.pop(f"forum::{forum}", None)
    summary["errors"] = summary_errors
    summary["total_records_after"] = sum(
        1
        for path in crawler.OUT_DIR.glob("*.json")
        if not path.name.startswith("_")
    )
    summary["manual_assertion_recovery"] = {
        "audited": len(audit_rows),
        "accepted_forums": accepted_forums,
        "decision_source": MANUAL_VERSION,
        "audit_path": str(args.audit_path.resolve()),
    }
    crawler.write_json(crawler.SUMMARY_PATH, summary)

    print(
        json.dumps(
            {
                "audited": len(audit_rows),
                "accepted_manual_surveys": accepted_forums,
                "written": written,
                "audit_path": str(args.audit_path.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
