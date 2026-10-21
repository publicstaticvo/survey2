#!/usr/bin/env python3
"""Knowledge contribution review state; extends the vendored ProReviewer CLI."""
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

from pydantic import BaseModel, ConfigDict, Field, field_validator
import proreviewer_cli as base
from reviewer_memory import ReviewLog, ReviewOutline, OutlineItem, validate_score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Context(Record):
    paper_path: str = ""
    sha256: str = ""
    publication_date: date | None = None
    date_basis: str = ""
    version: str = ""
    date_uncertainty: str = ""


class Evidence(Record):
    id: str = ""
    kind: str = "paper"
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    doi: str = ""
    url: str = ""
    version: str = ""
    available_date: date | None = None
    date_basis: str = ""
    location: str
    excerpt: str
    purpose: str
    status: str = "partial"
    search_ids: list[str] = Field(default_factory=list)
    accessed_at: str = ""


class Contribution(Record):
    id: str = ""
    statement: str
    paper_locations: list[str]
    baseline_or_prior: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    correctness_status: str = "unchecked"
    increment_status: str = "unchecked"
    significance_status: str = "unchecked"
    centrality: str = "unknown"
    dependencies: list[str] = Field(default_factory=list)
    counter_evidence_ids: list[str] = Field(default_factory=list)
    reason: str = ""
    uncertainty: str = ""


class ExpectedContribution(Record):
    id: str = ""
    expectation: str
    origins: list[str]
    basis_evidence_ids: list[str]
    scope: str
    necessity: str = "unknown"
    impact_hypothesis: str = ""
    tier: str = "exploratory"
    independence_reason: str = ""
    search_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    presence_status: str = "unchecked"
    rationality_status: str = "unchecked"
    missing_status: str = "unchecked"
    checked_locations: list[str] = Field(default_factory=list)
    counter_evidence_ids: list[str] = Field(default_factory=list)
    uncertainty: str = ""
    next_question: str = ""


class Search(Record):
    id: str = ""
    query: str
    query_target: str
    tool: str
    mode: str = "unknown"
    executed_at: str = ""
    urls: list[str] = Field(default_factory=list)
    status: str
    failure_reason: str = ""


class Item(OutlineItem):
    evidence_refs: list[str] = Field(default_factory=list)


class Outline(ReviewOutline):
    strengths: list[Item] = Field(default_factory=list)
    weaknesses: list[Item] = Field(default_factory=list)
    questions: list[Item] = Field(default_factory=list)
    comments: list[Item] = Field(default_factory=list)

    @field_validator("strengths", "weaknesses", "questions", "comments", mode="before")
    @classmethod
    def convert_to_outline_items(cls, value):
        return [x if isinstance(x, Item) else Item(**(x.model_dump() if isinstance(x, OutlineItem) else x))
                for x in value]


class Log(ReviewLog):
    context: Context = Field(default_factory=Context)
    contributions: list[Contribution] = Field(default_factory=list)
    expectations: list[ExpectedContribution] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    searches: list[Search] = Field(default_factory=list)
    review_outline: Outline = Field(default_factory=Outline)
    overall_reason: str = ""
    overall_refs: list[str] = Field(default_factory=list)
    limitations: str = ""


def load(output_dir):
    return Log.model_validate_json((Path(output_dir) / base.STATE_FILE).read_text(encoding="utf-8"))


def save(log, output_dir):
    path = Path(output_dir) / base.STATE_FILE
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(base._strip_rl_fields(log.model_dump(mode="json")),
                                    ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def all_records(log):
    return {r.id: r for key in ("claims", "questions", "notes", "contributions", "expectations", "evidence", "searches")
            for r in getattr(log, key)}


def refs(item):
    return item.related_claims + item.related_questions + item.related_notes + getattr(item, "evidence_refs", [])


def evidence_eligible(log, record):
    if record.kind == "paper":
        return record.status == "verified" and bool(record.location.strip() and record.excerpt.strip())
    return (record.kind == "external" and record.status == "verified"
            and bool(record.url and record.version and record.date_basis)
            and bool(record.location.strip() and record.excerpt.strip())
            and record.available_date is not None and log.context.publication_date is not None
            and record.available_date <= log.context.publication_date)


def audit(log, final=False):
    errors = []
    records = all_records(log)
    def check(ids, owner):
        for ref in ids:
            if ref not in records:
                errors.append(f"{owner}: unknown reference {ref}")
    def check_type(ids, allowed, owner):
        check(ids, owner)
        for ref in ids:
            if ref in records and not isinstance(records[ref], allowed):
                errors.append(f"{owner}: inappropriate reference type {ref}")
    for r in log.evidence:
        check_type(r.search_ids, Search, r.id)
        if r.kind not in ("paper", "external"):
            errors.append(f"{r.id}: kind must be paper or external")
        if r.status not in ("verified", "partial", "not_accessible", "provider_error", "excluded"):
            errors.append(f"{r.id}: invalid evidence status")
        if r.kind == "external" and r.status == "verified" and not evidence_eligible(log, r):
            errors.append(f"{r.id}: verified external evidence needs version, date basis, URL, full-text location/excerpt and availability <= publication date")
        if r.kind == "paper" and r.status == "verified" and not evidence_eligible(log, r):
            errors.append(f"{r.id}: verified paper evidence needs a location and excerpt")
    for key in ("contributions", "expectations"):
        for r in getattr(log, key):
            check_type(r.evidence_ids + r.counter_evidence_ids, Evidence, r.id)
            if key == "contributions":
                check_type(r.dependencies, Contribution, r.id)
            else:
                check(r.basis_evidence_ids, r.id)
                check_type(r.search_ids, Search, r.id)
                if not r.origins or any(x not in ("A", "B", "C", "D") for x in r.origins):
                    errors.append(f"{r.id}: origins must contain A/B/C/D")
                if r.tier not in ("exploratory", "decision_relevant"):
                    errors.append(f"{r.id}: invalid tier")
                if r.tier == "decision_relevant" and not r.independence_reason.strip():
                    errors.append(f"{r.id}: explain independence of expectation grounds")
    for section in ("strengths", "weaknesses", "questions", "comments"):
        for item in getattr(log.review_outline, section):
            check(refs(item), section)
            if not refs(item):
                errors.append(f"{section}: each review point needs evidence references")
    check(log.overall_refs, "overall judgment")
    if final:
        if log.review_outline.overall_score is not None:
            try:
                validate_score(log.review_outline.overall_score, log.conference)
            except ValueError as exc:
                errors.append(str(exc))
        if not log.context.publication_date or not log.context.date_basis.strip():
            errors.append("Confirm publication_date and date_basis before finalizing")
        if not log.review_outline.summary.strip():
            errors.append("Review summary is required")
        if not log.overall_reason.strip() or not log.overall_refs:
            errors.append("Overall judgment needs a reason and decisive references")
        if log.review_outline.overall_score is None and not log.limitations.strip():
            errors.append("Set an overall score or explain inability to judge in limitations")
        # Follow transitive links so post-cutoff evidence cannot hide behind a note or contribution.
        roots = [(ref, True) for ref in log.overall_refs]
        for section in ("strengths", "weaknesses", "questions", "comments"):
            for item in getattr(log.review_outline, section):
                roots.extend((ref, section == "weaknesses") for ref in refs(item))
        visited = set()
        def walk(ref, decisive):
            if (ref, decisive) in visited or ref not in records:
                return
            visited.add((ref, decisive))
            r = records[ref]
            if isinstance(r, Evidence):
                if r.kind == "external" and not evidence_eligible(log, r):
                    errors.append(f"{ref}: ineligible external evidence referenced by final review")
            elif isinstance(r, Contribution):
                if decisive and not r.evidence_ids:
                    errors.append(f"{ref}: decisive contribution needs source evidence")
                for child in r.evidence_ids + r.counter_evidence_ids + r.dependencies:
                    walk(child, decisive)
            elif isinstance(r, ExpectedContribution):
                if decisive and r.tier != "decision_relevant":
                    errors.append(f"{ref}: exploratory expectation cannot determine overall judgment")
                if decisive and len(set(r.basis_evidence_ids)) < 2:
                    errors.append(f"{ref}: decisive expectation needs independent grounds")
                if decisive and r.missing_status == "confirmed" and not r.checked_locations:
                    errors.append(f"{ref}: confirmed absence needs checked_locations")
                for child in r.basis_evidence_ids + r.evidence_ids + r.counter_evidence_ids:
                    walk(child, decisive)
        for ref, decisive in roots:
            walk(ref, decisive)
    return errors


def audit_files(log, output):
    errors = []
    text = (Path(output) / base.PAPER_FILE).read_text(encoding="utf-8")
    normalize = lambda s: re.sub(r"\s+", "", s)
    for record in log.evidence:
        if record.kind == "paper" and record.status == "verified":
            page = re.search(r"\bp\.?\s*(\d+)\b", record.location, re.I)
            scope = text
            if page and "<!-- page " in text:
                match = re.search(rf"<!-- page {int(page[1])} -->\n(.*?)(?=<!-- page |\Z)", text, re.S)
                if not match:
                    errors.append(f"{record.id}: nonexistent PDF page")
                    continue
                scope = match[1]
            if not normalize(record.excerpt) or normalize(record.excerpt) not in normalize(scope):
                errors.append(f"{record.id}: excerpt not found in paper at claimed page (whitespace ignored)")
    manifest = Path(output) / "input_manifest.json"
    if manifest.exists():
        saved = json.loads(manifest.read_text(encoding="utf-8"))
        if hashlib.sha256((Path(output) / base.PAPER_FILE).read_bytes()).hexdigest() != saved["text_sha256"]:
            errors.append("paper.md changed since initialization; initialize a separate run for another version")
        if log.context.sha256 != saved["sha256"]:
            errors.append("Input context fingerprint differs from initialization manifest")
        source = Path(saved["paper_path"])
        if source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest() != saved["sha256"]:
            errors.append("Original input file changed since initialization")
    return errors


def format_review(log, include_evidence=True):
    text = ORIGINAL_FORMAT(log, include_evidence)
    context = log.context
    header = (f"# Survey review\n\nPublication cutoff: {context.publication_date or 'unconfirmed'}\n\n"
              f"Date basis: {context.date_basis}\n\nTarget version: {context.version or 'see input fingerprint'}\n\n"
              f"Input SHA-256: `{context.sha256}`\n\n")
    extra = []
    if log.review_outline.comments:
        extra += ["## Comments", ""] + ["- " + (base._format_item_with_links(x) if include_evidence else x.text) for x in log.review_outline.comments]
    extra += ["\n## Overall judgment rationale\n", log.overall_reason,
              "\nDecisive records: " + ", ".join(f"[{r}](#{r.lower()})" if include_evidence else r for r in log.overall_refs)]
    if log.limitations:
        extra += ["\n## Investigation limitations\n", log.limitations]
    if include_evidence:
        # The upstream appendix includes C/Q/N from the three original outline lists.
        # Also include records cited only by comments or the overall rationale.
        original_refs = {r for section in ("strengths", "weaknesses", "questions")
                         for item in getattr(log.review_outline, section) for r in refs(item)}
        additional_refs = set(log.overall_refs)
        for item in log.review_outline.comments:
            additional_refs.update(refs(item))
        for r in sorted(additional_refs - original_refs):
            record = all_records(log).get(r)
            if r.startswith(("C", "Q", "N")) and record is not None:
                extra += [f'<a id="{r.lower()}"></a>\n### {r}\n',
                          "```json\n" + record.model_dump_json(indent=2) + "\n```\n"]
        extra += ["\n## Contribution and external evidence records\n"]
        # Keep exploratory/excluded material in the working log, not in the review.
        records = all_records(log)
        needed = set(original_refs) | additional_refs
        pending = list(needed)
        while pending:
            record = records.get(pending.pop())
            children = []
            if isinstance(record, Contribution):
                children = record.evidence_ids + record.counter_evidence_ids + record.dependencies
            elif isinstance(record, ExpectedContribution):
                children = record.basis_evidence_ids + record.evidence_ids + record.counter_evidence_ids + record.search_ids
            elif isinstance(record, Evidence):
                children = record.search_ids
            for child in children:
                if child not in needed:
                    needed.add(child)
                    pending.append(child)
        for key in ("contributions", "expectations", "evidence", "searches"):
            for record in getattr(log, key):
                if record.id not in needed:
                    continue
                extra += [f'<a id="{record.id.lower()}"></a>\n### {record.id}\n',
                          "```json\n" + record.model_dump_json(indent=2) + "\n```\n"]
    return header + text + "\n" + "\n".join(extra)


def init(args):
    # Validate metadata before touching the output directory.
    context = Context(publication_date=args.publication_date, date_basis=args.date_basis,
                      version=args.version, date_uncertainty=args.date_uncertainty)
    if context.publication_date and not context.date_basis.strip():
        raise ValueError("--publication-date requires --date-basis (user instruction or source)")
    base.cmd_init(args)
    output = args.dir or str(Path.cwd() / base.make_output_dir_name(args.paper))
    log = load(output)
    paper = Path(args.paper).resolve()
    context.paper_path = str(paper)
    if paper.is_file():
        context.sha256 = hashlib.sha256(paper.read_bytes()).hexdigest()
    log.context = context
    save(log, output)
    (Path(output) / "input_manifest.json").write_text(json.dumps({
        "paper_path": context.paper_path, "sha256": context.sha256,
        "text_sha256": hashlib.sha256((Path(output) / base.PAPER_FILE).read_bytes()).hexdigest(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Publication cutoff:", context.publication_date or "UNCONFIRMED: resolve before external evaluation")


def payload(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def run_custom(args):
    output = base.get_output_dir(args)
    log = load(output)
    if args.command == "context":
        data = payload(args.file)
        if set(data) - {"publication_date", "date_basis", "version", "date_uncertainty"}:
            raise ValueError("Context updates accept publication_date, date_basis, version, date_uncertainty")
        log.context = Context(**(log.context.model_dump() | data))
    elif args.command == "put":
        kinds = {"contribution": ("contributions", Contribution, "K"),
                 "expectation": ("expectations", ExpectedContribution, "X"),
                 "evidence": ("evidence", Evidence, "E"), "search": ("searches", Search, "S")}
        key, model, prefix = kinds[args.kind]
        data = payload(args.file)
        entries = getattr(log, key)
        existing = next((r for r in entries if r.id == data.get("id")), None)
        if data.get("id") and existing is None:
            raise ValueError("To create a record omit id; IDs are assigned by the CLI")
        data = (existing.model_dump() if existing else {}) | data
        data["id"] = existing.id if existing else f"{prefix}{len(entries)+1}"
        if args.kind in ("search", "evidence") and not data.get("executed_at" if args.kind == "search" else "accessed_at"):
            data["executed_at" if args.kind == "search" else "accessed_at"] = datetime.now(timezone.utc).isoformat()
        record = model(**data)
        if existing:
            entries[entries.index(existing)] = record
        else:
            entries.append(record)
        print(record.id)
    elif args.command == "judgment":
        data = payload(args.file)
        if set(data) - {"reason", "refs", "limitations"}:
            raise ValueError("Judgment fields: reason, refs, limitations")
        log.overall_reason = data["reason"]
        log.overall_refs = data["refs"]
        log.limitations = data.get("limitations", "")
    elif args.command == "point":
        item = Item(**payload(args.file))
        getattr(log.review_outline, args.section).append(item)
    elif args.command == "audit":
        errors = audit(log, final=True) + audit_files(log, output)
        print(json.dumps({"errors": errors}, ensure_ascii=False, indent=2))
        return 1 if errors else 0
    errors = audit(log) + audit_files(log, output)
    if errors:
        raise ValueError("\n".join(errors))
    save(log, output)
    return 0


ORIGINAL_FORMAT = base.format_review
base.ReviewLog = Log
base.load_log = load
base.save_log = save
base._item_refs = refs
base.format_review = format_review
ORIGINAL_SHOW = base.cmd_show
ORIGINAL_FINALIZE = base.cmd_finalize
ORIGINAL_EXPORT = base.cmd_export


def pdf_text(path):
    import pymupdf
    with pymupdf.open(path) as doc:
        return "\n\n".join(f"<!-- page {i+1} -->\n{page.get_text(sort=True)}" for i, page in enumerate(doc))


base.convert_pdf_to_text = pdf_text


def finalize(args):
    output = base.get_output_dir(args)
    log = load(output)
    errors = audit(log, final=True) + audit_files(log, output)
    if errors:
        raise ValueError("\n".join(errors))
    ORIGINAL_FINALIZE(args)


def export(args):
    output = base.get_output_dir(args)
    log = load(output)
    errors = audit(log, final=True) + audit_files(log, output)
    if errors:
        raise ValueError("\n".join(errors))
    ORIGINAL_EXPORT(args)


def show(args):
    ORIGINAL_SHOW(args)
    log = load(base.get_output_dir(args))
    print(json.dumps({"context": log.context.model_dump(mode="json"),
                      **{key: [x.model_dump(mode="json") for x in getattr(log, key)]
                         for key in ("contributions", "expectations", "evidence", "searches")}},
                     ensure_ascii=False, indent=2))


def main():
    argv = sys.argv[1:]
    if not argv or argv == ["--help"] or argv == ["-h"]:
        print("Survey review CLI: ProReviewer commands plus context, put, point, judgment, audit.\n"
              "Use init --help for publication date options; <command> --help for details.")
        return 0
    custom = argparse.ArgumentParser(add_help=False)
    custom.add_argument("--dir")
    commands = custom.add_subparsers(dest="command")
    p = commands.add_parser("init")
    p.add_argument("paper")
    p.add_argument("--dir", default=argparse.SUPPRESS)
    p.add_argument("--conference", default=base.DEFAULT_CONFERENCE, choices=list(base.CONFERENCE_SCALES))
    p.add_argument("--force", action="store_true")
    p.add_argument("--publication-date")
    p.add_argument("--date-basis", default="")
    p.add_argument("--version", default="")
    p.add_argument("--date-uncertainty", default="")
    for name in ("context", "judgment", "point", "put", "audit"):
        p = commands.add_parser(name)
        if name != "audit":
            p.add_argument("--file", required=True)
        if name == "point":
            p.add_argument("--section", required=True, choices=["strengths", "weaknesses", "questions", "comments"])
        if name == "put":
            p.add_argument("kind", choices=["contribution", "expectation", "evidence", "search"])
    # Delegate unchanged commands to ProReviewer, including its help and argument forms.
    command = next((x for i, x in enumerate(argv) if not x.startswith("-") and (i == 0 or argv[i-1] != "--dir")), "")
    if command not in ("init", "context", "judgment", "point", "put", "audit"):
        base.cmd_show = show
        base.cmd_finalize = finalize
        base.cmd_export = export
        base.main()
        return 0
    args = custom.parse_args(argv)
    if args.command == "init":
        # Avoid recursive replacement of base init.
        init(args)
        return 0
    return run_custom(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
