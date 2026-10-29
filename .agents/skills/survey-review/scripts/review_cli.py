#!/usr/bin/env python3
"""CLI for evidence-traceable survey review state."""

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

import review_support as base


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Context(StrictModel):
    paper_path: str = ""
    sha256: str = ""
    publication_date: date | None = None
    date_basis: str = ""
    version: str = ""
    date_uncertainty: str = ""


class Entry(StrictModel):
    id: str
    data: dict = Field(default_factory=dict)


class Log(StrictModel):
    schema_version: int = 3
    conference: str = "iclr"
    context: Context = Field(default_factory=Context)
    knowledge_units: list[Entry] = Field(default_factory=list)
    expectations: list[Entry] = Field(default_factory=list)
    evidence: list[Entry] = Field(default_factory=list)
    assessments: list[Entry] = Field(default_factory=list)
    searches: list[Entry] = Field(default_factory=list)
    impacts: list[Entry] = Field(default_factory=list)
    review_outline: dict = Field(default_factory=lambda: {
        "summary": "",
        "overall_score": None,
        "strengths": [],
        "weaknesses": [],
        "questions": [],
        "comments": [],
    })
    overall_reason: str = ""
    overall_refs: list[str] = Field(default_factory=list)
    scale_reason: str = ""
    limitations: str = ""


KINDS = {
    "knowledge": ("knowledge_units", "K"),
    "expectation": ("expectations", "X"),
    "evidence": ("evidence", "E"),
    "assessment": ("assessments", "A"),
    "search": ("searches", "S"),
    "impact": ("impacts", "I"),
}

UPDATE_COMMANDS = {
    "update_knowledge": ("knowledge_units", "K"),
    "update_expectation": ("expectations", "X"),
    "update_impact": ("impacts", "I"),
}

STATUS_VALUES = {
    "increment_identification": {"unchecked", "possible_increment", "not_increment", "unknown"},
    "correctness": {"unchecked", "supported", "qualified", "invalid", "unknown", "skipped"},
    "novelty": {"unchecked", "prior_match", "partial_overlap", "no_match_within_search", "unknown", "skipped"},
    "value": {"unchecked", "meaningful", "limited", "not_established", "unknown", "skipped"},
    "rationality": {"pending", "confirmed", "rejected", "insufficient"},
    "presence": {"unchecked", "present", "partial", "absent", "unknown"},
}

REF_FIELDS = (
    "evidence_refs",
    "assessment_refs",
    "search_refs",
    "target_refs",
    "counter_evidence_refs",
    "overlaps",
    "related_knowledge_ids",
    "checked_source_refs",
)

REQUIRED_FIELDS = {
    "knowledge_units": {
        "statement", "scope", "paper_locations", "result_form",
        "knowledge_relation", "extraction_reason",
        "increment_identification_status", "correctness_status",
        "novelty_status", "value_status", "evidence_refs",
        "assessment_refs", "promise_refs", "related_knowledge_ids",
    },
    "expectations": {
        "expectation", "route", "trigger_reason", "scope", "scholarly_use",
        "rationale", "feasible_response", "rationality_status", "presence_status",
    },
    "evidence": {
        "source_type", "source_identity", "version_date", "location", "excerpt",
        "role", "evaluation_role", "target_refs", "accessed_at", "cutoff_eligible",
    },
    "assessments": {
        "target_id", "dimension", "question", "status", "reason", "evidence_refs",
        "counter_evidence_refs", "unresolved", "cutoff",
    },
    "searches": {"target_question", "query", "tool", "status", "searched_at"},
    "impacts": {
        "finding", "target_refs", "evidence_refs", "direction", "extent",
        "effect", "reason", "status",
    },
}

DEFAULT_FIELDS = {
    "knowledge": {
        "increment_identification_status": "unchecked",
        "correctness_status": "unchecked",
        "novelty_status": "unchecked",
        "value_status": "unchecked",
        "evidence_refs": [],
        "assessment_refs": [],
        "promise_refs": [],
        "related_knowledge_ids": [],
    },
    "expectation": {
        "rationality_status": "pending",
        "presence_status": "unchecked",
        "evidence_refs": [],
        "search_refs": [],
        "related_knowledge_ids": [],
    },
    "evidence": {"target_refs": []},
    "assessment": {
        "evidence_refs": [],
        "counter_evidence_refs": [],
        "unresolved": "",
    },
    "search": {"result_urls": [], "checked_source_refs": []},
    "impact": {"uncertainty": "", "overlaps": []},
}

ASSESSMENT_FIELDS = {
    "increment_identification": "increment_identification_status",
    "correctness": "correctness_status",
    "novelty": "novelty_status",
    "value": "value_status",
}


def run_dir(args: argparse.Namespace) -> Path:
    if not args.dir:
        raise ValueError("--dir is required for this command")
    path = Path(args.dir).resolve()
    if not path.is_dir():
        raise ValueError(f"review directory does not exist: {path}")
    return path


def load_log(path: Path) -> Log:
    state = path / base.STATE_FILE
    if not state.is_file():
        raise ValueError(f"missing {base.STATE_FILE}: {path}")
    return Log.model_validate_json(state.read_text(encoding="utf-8"))


def save_log(log: Log, path: Path) -> None:
    base.atomic_json(path / base.STATE_FILE, log.model_dump(mode="json"))


def read_payload(path: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


def safe_stem(stem: str) -> str:
    cleaned = re.sub(r'[<>:"/\\\\|?*]', "_", stem)
    cleaned = cleaned.rstrip(" .")
    if not cleaned:
        raise ValueError("paper filename has no usable stem")
    return cleaned


def init_review(args: argparse.Namespace) -> None:
    source = base.resolve_input(args.paper)
    expected_name = f"review_{safe_stem(source.stem)}"
    output_parent = Path(args.output_parent).resolve() if args.output_parent else source.parent
    if not output_parent.is_dir():
        raise ValueError(f"output parent does not exist: {output_parent}")
    output = output_parent / expected_name
    if output.exists():
        raise ValueError(f"review directory already exists: {output}")
    manuscript, sources = base.read_manuscript(source)
    output.mkdir(parents=True)
    (output / "inputs").mkdir()
    (output / "sources").mkdir()
    paper_path = output / base.PAPER_FILE
    paper_path.write_text(manuscript, encoding="utf-8")
    context = Context(
        paper_path=str(paper_path.resolve()),
        sha256=hashlib.sha256(manuscript.encode("utf-8")).hexdigest(),
        publication_date=args.publication_date,
        date_basis=args.date_basis,
        version=args.version,
        date_uncertainty=args.date_uncertainty,
    )
    save_log(Log(conference=args.conference, context=context), output)
    base.atomic_json(output / "input_manifest.json", {"input": str(source), "sources": sources})
    print(output)


def entries(log: Log, field: str) -> list[Entry]:
    return getattr(log, field)


def next_id(log: Log, field: str, prefix: str) -> str:
    used = {entry.id for entry in entries(log, field)}
    number = 1
    while f"{prefix}{number}" in used:
        number += 1
    return f"{prefix}{number}"


def ensure_id(log: Log, field: str, prefix: str, supplied: str | None) -> str:
    ident = supplied or next_id(log, field, prefix)
    if not re.fullmatch(rf"{re.escape(prefix)}[1-9][0-9]*", ident):
        raise ValueError(f"invalid {prefix} identifier: {ident}")
    if any(entry.id == ident for entry in entries(log, field)):
        raise ValueError(f"identifier already exists: {ident}")
    return ident


def create_entry(log: Log, kind: str, payload: dict) -> str:
    field, prefix = KINDS[kind]
    ident = ensure_id(log, field, prefix, payload.pop("id", None))
    data = {**DEFAULT_FIELDS.get(kind, {}), **payload}
    entries(log, field).append(Entry(id=ident, data=data))
    return ident


def update_entry(log: Log, field: str, ident: str, patch: dict) -> None:
    found = next((entry for entry in entries(log, field) if entry.id == ident), None)
    if found is None:
        raise ValueError(f"record not found: {ident}")
    if "id" in patch and patch["id"] != ident:
        raise ValueError("an update cannot change the record identifier")
    patch.pop("id", None)
    if "revision_history" in patch:
        raise ValueError("revision_history is maintained by the CLI")
    history = list(found.data.get("revision_history", []))
    history.append({
        "changes": {
            key: {"present": key in found.data, "value": copy.deepcopy(found.data.get(key))}
            for key in patch
        }
    })
    found.data.update(patch)
    found.data["revision_history"] = history


def validate_references(log: Log, data: dict) -> None:
    known = all_ids(log)
    for field in REF_FIELDS:
        value = data.get(field, [])
        if value in (None, ""):
            continue
        refs = value if isinstance(value, list) else [value]
        if not all(isinstance(ref, str) for ref in refs):
            raise ValueError(f"{field} must contain record identifiers")
        missing = [ref for ref in refs if ref not in known]
        if missing:
            raise ValueError(f"{field} references missing records: {', '.join(missing)}")


def command_create(args: argparse.Namespace, kind: str) -> None:
    path = run_dir(args)
    log = load_log(path)
    payload = read_payload(args.file)
    ident = create_entry(log, kind, payload)
    errors = validate_log(log)
    if errors:
        raise ValueError("invalid record: " + "; ".join(errors))
    save_log(log, path)
    print(ident)


def command_update(args: argparse.Namespace, command: str) -> None:
    path = run_dir(args)
    log = load_log(path)
    field, prefix = UPDATE_COMMANDS[command]
    if not args.id.startswith(prefix):
        raise ValueError(f"{command} requires a {prefix} identifier")
    update_entry(log, field, args.id, read_payload(args.file))
    errors = validate_log(log)
    if errors:
        raise ValueError("invalid update: " + "; ".join(errors))
    save_log(log, path)
    print(args.id)


def command_assess(args: argparse.Namespace) -> None:
    path = run_dir(args)
    log = load_log(path)
    payload = {**DEFAULT_FIELDS["assessment"], **read_payload(args.file)}
    target = payload.get("target_id")
    dimension = payload.get("dimension")
    if not isinstance(target, str) or not isinstance(dimension, str):
        raise ValueError("assessment requires target_id and dimension")
    if not find_record(log, target):
        raise ValueError(f"assessment target not found: {target}")
    if dimension not in STATUS_VALUES:
        raise ValueError(f"unknown assessment dimension: {dimension}")
    expected_dimensions = {
        "K": {"increment_identification", "correctness", "novelty", "value"},
        "X": {"rationality", "presence"},
    }
    target_prefix = target[0] if target else ""
    if dimension not in expected_dimensions.get(target_prefix, set()):
        raise ValueError(f"{dimension} cannot assess target {target}")
    status = payload.get("status")
    if not isinstance(status, str) or status not in STATUS_VALUES[dimension]:
        raise ValueError(f"invalid {dimension} status: {status}")
    if not payload.get("question") or not payload.get("reason") or not payload.get("cutoff"):
        raise ValueError("assessment requires question, reason and cutoff")
    existing = next(
        (entry for entry in log.assessments
         if entry.data.get("target_id") == target and entry.data.get("dimension") == dimension),
        None,
    )
    if existing is None:
        ident = ensure_id(log, "assessments", "A", payload.pop("id", None))
        log.assessments.append(Entry(id=ident, data=payload))
    else:
        ident = existing.id
        update_entry(log, "assessments", ident, payload)
    target_entry = find_record(log, target)
    assert target_entry is not None
    refs = list(target_entry.data.get("assessment_refs", []))
    if ident not in refs:
        refs.append(ident)
    target_entry.data["assessment_refs"] = refs
    if target.startswith("K"):
        field_name = {
            "increment_identification": "increment_identification_status",
            "correctness": "correctness_status",
            "novelty": "novelty_status",
            "value": "value_status",
        }.get(dimension)
        if field_name:
            target_entry.data[field_name] = status
            if status == "skipped":
                skip_reasons = dict(target_entry.data.get("skip_reasons", {}))
                skip_reasons[dimension] = payload.get("skip_reason", "")
                target_entry.data["skip_reasons"] = skip_reasons
    elif target.startswith("X"):
        field_name = {"rationality": "rationality_status", "presence": "presence_status"}.get(dimension)
        if field_name:
            target_entry.data[field_name] = status
    errors = validate_log(log)
    if errors:
        raise ValueError("invalid assessment: " + "; ".join(errors))
    save_log(log, path)
    print(ident)


def find_record(log: Log, ident: str) -> Entry | None:
    for field, _ in KINDS.values():
        found = next((entry for entry in entries(log, field) if entry.id == ident), None)
        if found is not None:
            return found
    return None


def all_ids(log: Log) -> set[str]:
    result = set()
    for field, _ in KINDS.values():
        result.update(entry.id for entry in entries(log, field))
    return result


def referenced_ids(log: Log, data: dict) -> list[str]:
    refs = []
    for field in REF_FIELDS:
        value = data.get(field, [])
        if isinstance(value, list):
            refs.extend(value)
        elif value:
            refs.append(value)
    return [value for value in refs if isinstance(value, str)]


def validate_log(log: Log, final: bool = False) -> list[str]:
    errors = []
    if not log.context.paper_path:
        errors.append("context.paper_path is required")
    elif not Path(log.context.paper_path).is_file():
        errors.append("context.paper_path does not exist")
    known = all_ids(log)
    seen: set[str] = set()
    for field, prefix in KINDS.values():
        for entry in entries(log, field):
            if entry.id in seen:
                errors.append(f"duplicate record ID: {entry.id}")
            seen.add(entry.id)
            if not entry.id.startswith(prefix):
                errors.append(f"{entry.id} has the wrong prefix for {field}")
            if not re.fullmatch(rf"{re.escape(prefix)}[1-9][0-9]*", entry.id):
                errors.append(f"{entry.id} is not a valid record ID")
            missing_fields = REQUIRED_FIELDS[field] - entry.data.keys()
            if missing_fields:
                errors.append(f"{entry.id} is missing fields: {', '.join(sorted(missing_fields))}")
            for ref in referenced_ids(log, entry.data):
                if ref not in known:
                    errors.append(f"{entry.id} references missing record {ref}")
            for ref_field in REF_FIELDS:
                value = entry.data.get(ref_field, [])
                if value in (None, ""):
                    continue
                refs = value if isinstance(value, list) else [value]
                if not all(isinstance(ref, str) for ref in refs):
                    errors.append(f"{entry.id} has invalid {ref_field}")
            if field == "knowledge_units":
                relation = entry.data.get("knowledge_relation")
                result_form = entry.data.get("result_form")
                if not isinstance(relation, str) or relation not in {
                    "background", "single_source_summary", "review_synthesis", "unresolved"
                }:
                    errors.append(f"{entry.id} has invalid knowledge_relation")
                if not isinstance(result_form, str) or result_form not in {"synthesis", "organization", "both"}:
                    errors.append(f"{entry.id} has invalid result_form")
                for dimension, status_field in ASSESSMENT_FIELDS.items():
                    value = entry.data.get(status_field)
                    if not isinstance(value, str) or value not in STATUS_VALUES[dimension]:
                        errors.append(f"{entry.id} has invalid {dimension} status")
            elif field == "expectations":
                if entry.data.get("route") not in {"ordinary_reader", "senior_reader"}:
                    errors.append(f"{entry.id} has invalid route")
                rationality = entry.data.get("rationality_status")
                presence = entry.data.get("presence_status")
                if not isinstance(rationality, str) or rationality not in STATUS_VALUES["rationality"]:
                    errors.append(f"{entry.id} has invalid rationality_status")
                if not isinstance(presence, str) or presence not in STATUS_VALUES["presence"]:
                    errors.append(f"{entry.id} has invalid presence_status")
            elif field == "evidence":
                if entry.data.get("role") not in {"support", "counter", "limit", "context"}:
                    errors.append(f"{entry.id} has invalid role")
                if entry.data.get("evaluation_role") not in {
                    "increment", "correctness", "novelty", "value", "expectation", "impact"
                }:
                    errors.append(f"{entry.id} has invalid evaluation_role")
                if entry.data.get("cutoff_eligible") not in {"yes", "no", "unknown"}:
                    errors.append(f"{entry.id} has invalid cutoff_eligible")
            elif field == "searches" and entry.data.get("status") not in {
                "success", "no_results", "partial", "failed"
            }:
                errors.append(f"{entry.id} has invalid search status")
            elif field == "impacts":
                if entry.data.get("direction") not in {"supports", "qualifies", "limits", "harms"}:
                    errors.append(f"{entry.id} has invalid direction")
                if entry.data.get("extent") not in {"local", "supporting", "main", "independent_quality"}:
                    errors.append(f"{entry.id} has invalid extent")
                if entry.data.get("status") not in {"established", "uncertain", "withdrawn"}:
                    errors.append(f"{entry.id} has invalid impact status")
    for entry in log.assessments:
        target = entry.data.get("target_id")
        dimension = entry.data.get("dimension")
        status = entry.data.get("status")
        if not isinstance(target, str) or target not in known:
            errors.append(f"{entry.id} has missing target_id")
        if not isinstance(dimension, str) or dimension not in STATUS_VALUES:
            errors.append(f"{entry.id} has invalid dimension")
        elif not isinstance(status, str) or status not in STATUS_VALUES[dimension]:
            errors.append(f"{entry.id} has invalid status for {dimension}")
        elif isinstance(target, str) and target in known:
            valid_target_dimensions = {
                "K": {"increment_identification", "correctness", "novelty", "value"},
                "X": {"rationality", "presence"},
            }
            if dimension not in valid_target_dimensions.get(target[0], set()):
                errors.append(f"{entry.id} has a dimension that does not apply to {target}")
        if status == "unknown" and not entry.data.get("evidence_refs") and not entry.data.get("unresolved"):
            errors.append(f"{entry.id} unknown needs evidence_refs or unresolved reason")
        if status == "skipped" and not entry.data.get("skip_reason"):
            errors.append(f"{entry.id} skipped needs skip_reason")
        if target and isinstance(target, str) and target.startswith("K") and dimension == "increment_identification" and status == "skipped":
            errors.append(f"{entry.id} increment identification cannot be skipped")
        if target and isinstance(target, str) and target.startswith("X") and dimension == "rationality" and status not in STATUS_VALUES["rationality"]:
            errors.append(f"{entry.id} has invalid expectation rationality")
    if final:
        for knowledge in log.knowledge_units:
            for dimension, field_name in ASSESSMENT_FIELDS.items():
                status = knowledge.data.get(field_name, "unchecked")
                if status == "unchecked":
                    errors.append(f"{knowledge.id} has unchecked {dimension}")
                    continue
                if status == "skipped":
                    if dimension == "increment_identification":
                        errors.append(f"{knowledge.id} cannot skip knowledge-increment identification")
                    reason = knowledge.data.get("skip_reasons", {}).get(dimension)
                    if not reason:
                        errors.append(f"{knowledge.id} skipped {dimension} without a reason")
                assessment = next(
                    (item for item in log.assessments
                     if item.data.get("target_id") == knowledge.id
                     and item.data.get("dimension") == dimension),
                    None,
                )
                if assessment is None:
                    errors.append(f"{knowledge.id} lacks an assessment record for {dimension}")
                elif assessment.data.get("status") != status:
                    errors.append(f"{knowledge.id} {dimension} status differs from its assessment record")
                if status == "unknown":
                    if assessment is None or not (
                        assessment.data.get("evidence_refs") or assessment.data.get("unresolved")
                    ):
                        errors.append(f"{knowledge.id} unknown {dimension} lacks investigation detail")
        for expectation in log.expectations:
            rationality = expectation.data.get("rationality_status", "pending")
            presence = expectation.data.get("presence_status", "unchecked")
            if rationality == "pending":
                errors.append(f"{expectation.id} has pending rationality")
            rationality_assessment = next(
                (item for item in log.assessments
                 if item.data.get("target_id") == expectation.id
                 and item.data.get("dimension") == "rationality"),
                None,
            )
            if rationality_assessment is None:
                errors.append(f"{expectation.id} lacks a rationality assessment record")
            if rationality == "confirmed" and presence in ("unchecked", "unknown"):
                errors.append(f"{expectation.id} has incomplete presence check")
            if rationality == "confirmed" and not any(
                item.data.get("target_id") == expectation.id
                and item.data.get("dimension") == "presence"
                for item in log.assessments
            ):
                errors.append(f"{expectation.id} lacks a presence assessment record")
            if presence == "unknown" and not (
                expectation.data.get("evidence_refs") or expectation.data.get("search_refs")
                or expectation.data.get("uncertainty")
            ):
                errors.append(f"{expectation.id} unknown presence lacks investigation detail")
        for section in ("strengths", "weaknesses", "questions", "comments"):
            for index, point in enumerate(log.review_outline.get(section, []), start=1):
                if not point.get("evidence_refs"):
                    errors.append(f"{section}[{index}] needs evidence_refs")
                for ref in point.get("evidence_refs", []):
                    if ref not in known:
                        errors.append(f"{section}[{index}] references missing record {ref}")
    if final:
        if not log.review_outline.get("summary"):
            errors.append("final review needs review_outline.summary")
        if not log.overall_reason:
            errors.append("final review needs overall_reason")
        for ref in log.overall_refs:
            if ref not in known:
                errors.append(f"overall_reason references missing record {ref}")
    return sorted(set(errors))


def command_show(args: argparse.Namespace) -> None:
    path = run_dir(args)
    log = load_log(path)
    if args.detailed:
        print(log.model_dump_json(indent=2))
        return
    summary = {
        "schema_version": log.schema_version,
        "records": {field: len(entries(log, field)) for field, _ in KINDS.values()},
        "summary": log.review_outline.get("summary", ""),
        "overall_score": log.review_outline.get("overall_score"),
        "overall_reason": log.overall_reason,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def command_step(args: argparse.Namespace) -> None:
    path = run_dir(args)
    step_path = path / base.STEPS_FILE
    existing = [
        json.loads(line)
        for line in step_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if step_path.is_file() else []
    record = {
        "step": len(existing) + 1,
        "target": args.target,
        "why": args.why,
        "action": args.action,
        "found": args.found,
        "ops": [item.strip() for item in args.ops.split(";") if item.strip()] if args.ops else [],
    }
    with step_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    base.render_steps(path)
    print(record["step"])


def command_outline(args: argparse.Namespace) -> None:
    path = run_dir(args)
    log = load_log(path)
    if args.section == "summary":
        log.review_outline["summary"] = args.content
    elif args.section == "overall_score":
        score = float(args.content)
        base.validate_score(score, log.conference)
        log.review_outline["overall_score"] = int(score) if score.is_integer() else score
    else:
        raise ValueError("outline accepts summary or overall_score; use point for review points")
    save_log(log, path)


def command_point(args: argparse.Namespace) -> None:
    path = run_dir(args)
    log = load_log(path)
    payload = read_payload(args.file)
    if not payload.get("text"):
        raise ValueError("point requires text")
    refs = payload.get("evidence_refs", [])
    if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs):
        raise ValueError("point evidence_refs must be a list")
    missing = [ref for ref in refs if ref not in all_ids(log)]
    if missing:
        raise ValueError(f"point references missing records: {', '.join(missing)}")
    log.review_outline.setdefault(args.section, []).append(payload)
    save_log(log, path)


def command_judgment(args: argparse.Namespace) -> None:
    path = run_dir(args)
    log = load_log(path)
    payload = read_payload(args.file)
    if not payload.get("reason"):
        raise ValueError("judgment requires reason")
    refs = payload.get("refs", [])
    if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs):
        raise ValueError("judgment refs must be a list of record identifiers")
    missing = [ref for ref in refs if ref not in all_ids(log)]
    if missing:
        raise ValueError(f"judgment references missing records: {', '.join(missing)}")
    log.overall_reason = payload["reason"]
    log.overall_refs = refs
    log.scale_reason = payload.get("scale_reason", "")
    log.limitations = payload.get("limitations", "")
    save_log(log, path)


def render_review(log: Log) -> str:
    lines = ["# Survey review", "", "## Summary", "", log.review_outline.get("summary", ""), ""]
    for section in ("strengths", "weaknesses", "questions", "comments"):
        lines.extend([f"## {section.title()}", ""])
        points = log.review_outline.get(section, [])
        if not points:
            lines.extend(["No points recorded.", ""])
            continue
        for point in points:
            lines.append(f"- {point.get('text', '')}")
            if point.get("evidence_refs"):
                lines.append(f"  Evidence: {', '.join(point['evidence_refs'])}")
        lines.append("")
    score = log.review_outline.get("overall_score")
    lines.extend(["## Overall score", "", str(score if score is not None else "Not set"), "",
                  "## Overall reasoning", "", log.overall_reason, ""])
    if log.limitations:
        lines.extend(["## Limitations", "", log.limitations, ""])
    lines.extend(["## Evidence appendix", ""])
    for evidence in log.evidence:
        data = evidence.data
        lines.extend([
            f"### {evidence.id}",
            f"- Source: {data.get('source_identity', '')}",
            f"- Location: {data.get('location', '')}",
            f"- Role: {data.get('role', '')}",
            f"- Excerpt: {data.get('excerpt', '')}",
            "",
        ])
    return "\n".join(lines)


def command_validate(args: argparse.Namespace, final: bool = False) -> int:
    path = run_dir(args)
    log = load_log(path)
    errors = validate_log(log, final=final)
    print(json.dumps({"errors": errors}, ensure_ascii=False, indent=2))
    if errors:
        return 1
    return 0


def command_finalize(args: argparse.Namespace) -> int:
    path = run_dir(args)
    log = load_log(path)
    errors = validate_log(log, final=True)
    if errors:
        print(json.dumps({"errors": errors}, ensure_ascii=False, indent=2))
        return 1
    (path / base.REVIEW_FILE).write_text(render_review(log), encoding="utf-8")
    (path / "audit_summary.md").write_text("# Audit summary\n\nStructural validation passed.\n", encoding="utf-8")
    base.render_steps(path)
    print(path / base.REVIEW_FILE)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evidence-traceable survey review state")
    parser.add_argument("--dir", help="review_<paper stem> directory")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init")
    init_parser.add_argument("paper")
    init_parser.add_argument("--output-parent")
    init_parser.add_argument("--conference", default=base.DEFAULT_CONFERENCE, choices=list(base.CONFERENCE_SCALES))
    init_parser.add_argument("--publication-date", type=date.fromisoformat)
    init_parser.add_argument("--date-basis", default="")
    init_parser.add_argument("--version", default="")
    init_parser.add_argument("--date-uncertainty", default="")

    sub.add_parser("show").add_argument("--detailed", action="store_true")
    for command, kind in (
        ("add_knowledge", "knowledge"),
        ("add_expectation", "expectation"),
        ("add_evidence", "evidence"),
        ("record_search", "search"),
        ("add_impact", "impact"),
    ):
        item = sub.add_parser(command)
        item.add_argument("--file", required=True)
        item.set_defaults(record_kind=kind)
    for command in ("update_knowledge", "update_expectation", "update_impact"):
        item = sub.add_parser(command)
        item.add_argument("--id", required=True)
        item.add_argument("--file", required=True)
    assess = sub.add_parser("assess")
    assess.add_argument("--file", required=True)

    step = sub.add_parser("step")
    step.add_argument("--target", required=True)
    step.add_argument("--why", required=True)
    step.add_argument("--action", required=True)
    step.add_argument("--found", required=True)
    step.add_argument("--ops")

    outline = sub.add_parser("outline")
    outline.add_argument("--section", required=True, choices=("summary", "overall_score"))
    outline.add_argument("--content", required=True)
    point = sub.add_parser("point")
    point.add_argument("--section", required=True, choices=("strengths", "weaknesses", "questions", "comments"))
    point.add_argument("--file", required=True)
    judgment = sub.add_parser("judgment")
    judgment.add_argument("--file", required=True)
    sub.add_parser("validate")
    sub.add_parser("finalize")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "init":
        init_review(args)
        return 0
    if args.command == "show":
        command_show(args)
        return 0
    if args.command == "step":
        command_step(args)
        return 0
    if args.command == "outline":
        command_outline(args)
        return 0
    if args.command == "point":
        command_point(args)
        return 0
    if args.command == "judgment":
        command_judgment(args)
        return 0
    if args.command == "assess":
        command_assess(args)
        return 0
    if args.command == "validate":
        return command_validate(args)
    if args.command == "finalize":
        return command_finalize(args)
    if args.command.startswith("add_"):
        command_create(args, args.record_kind)
        return 0
    if args.command == "record_search":
        command_create(args, args.record_kind)
        return 0
    if args.command in UPDATE_COMMANDS:
        command_update(args, args.command)
        return 0
    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
