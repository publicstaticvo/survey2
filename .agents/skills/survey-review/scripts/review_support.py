"""Input conversion, rating interfaces and step rendering for survey review."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

STATE_FILE = "review_log.json"
PAPER_FILE = "paper.md"
REVIEW_FILE = "review.md"
STEPS_FILE = "steps.jsonl"
STEPS_MD = "steps.md"

CONFERENCE_SCALES: dict[str, dict] = {
    "iclr": {
        "name": "ICLR 2026",
        "scores": [0, 2, 4, 6, 8, 10],
        "labels": {
            10: "Strong accept  -  should be highlighted at the conference",
            8:  "Accept  -  good submission",
            6:  "Marginally above the acceptance threshold",
            4:  "Marginally below the acceptance threshold",
            2:  "Reject  -  not good enough",
            0:  "Strong reject",
        },
    },
    "icml": {
        "name": "ICML 2026",
        "scores": [1, 2, 3, 4, 5, 6],
        "labels": {
            6: "Strong Accept  -  technically flawless, exceptional impact",
            5: "Accept  -  technically solid, high impact",
            4: "Weak Accept  -  solid contribution, some weaknesses limit impact",
            3: "Weak Reject  -  clear merits but weaknesses outweigh",
            2: "Reject  -  e.g. technical flaws, weak evaluation, poor reproducibility",
            1: "Strong Reject  -  e.g. well-known results, impossible to judge contribution",
        },
    },
    "neurips": {
        "name": "NeurIPS 2026",
        "scores": [1, 2, 3, 4, 5, 6],
        "labels": {
            6: "Strong Accept  -  technically flawless, groundbreaking impact",
            5: "Accept  -  technically solid, high potential value",
            4: "Borderline Accept  -  acceptance reasons outweigh rejection reasons",
            3: "Borderline Reject  -  rejection reasons outweigh acceptance reasons",
            2: "Reject  -  technical flaws, weak evaluation, inadequate reproducibility",
            1: "Strong Reject  -  well-known results or unaddressed ethical considerations",
        },
    },
    "acl": {
        "name": "ACL (ARR)",
        "scores": [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5],
        "labels": {
            5:   "Consider for Award",
            4.5: "Borderline Award",
            4:   "Conference  -  could be accepted to an *ACL conference",
            3.5: "Borderline Conference",
            3:   "Findings  -  could be accepted to Findings of ACL",
            2.5: "Borderline Findings",
            2:   "Resubmit next cycle  -  needs substantial revisions",
            1.5: "Resubmit after next cycle  -  revisions cannot be completed in one cycle",
            1:   "Do not resubmit  -  paper has to be fully redone",
        },
    },
    "emnlp": {
        "name": "EMNLP (ARR)",
        "scores": [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5],
        "labels": {
            5:   "Consider for Award",
            4.5: "Borderline Award",
            4:   "Conference  -  could be accepted to an *ACL conference",
            3.5: "Borderline Conference",
            3:   "Findings  -  could be accepted to Findings of ACL",
            2.5: "Borderline Findings",
            2:   "Resubmit next cycle  -  needs substantial revisions",
            1.5: "Resubmit after next cycle  -  revisions cannot be completed in one cycle",
            1:   "Do not resubmit  -  paper has to be fully redone",
        },
    },
}

DEFAULT_CONFERENCE = "iclr"


def get_valid_scores(conference: str) -> list:
    """Return the list of valid score values for a conference."""
    key = conference.lower()
    if key not in CONFERENCE_SCALES:
        raise ValueError(
            f"Unknown conference '{conference}'. "
            f"Supported: {', '.join(CONFERENCE_SCALES.keys())}"
        )
    return CONFERENCE_SCALES[key]["scores"]


def validate_score(score, conference: str) -> None:
    """Raise ValueError if score is not valid for the conference scale."""
    valid = get_valid_scores(conference)
    if score not in valid:
        scale = CONFERENCE_SCALES[conference.lower()]
        raise ValueError(
            f"Score {score} is not valid for {scale['name']}. "
            f"Valid scores: {valid}"
        )


def format_score_with_scale(score, conference: str) -> str:
    """Format a score with its conference scale context."""
    key = conference.lower()
    scale = CONFERENCE_SCALES.get(key)
    if not scale:
        return str(score)
    label = scale["labels"].get(score, "")
    name = scale["name"]
    hi = max(scale["scores"])
    if label:
        return f"{score}/{hi} ({name}: {label})"
    return f"{score}/{hi} ({name})"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def resolve_input(paper):
    path = Path(paper).resolve()
    if path.is_dir():
        preferred = [path / name for name in ("main.tex", "paper.tex", "manuscript.tex")]
        chosen = next((p for p in preferred if p.is_file()), None)
        if chosen is None:
            candidates = list(path.glob("*.tex"))
            if len(candidates) != 1:
                raise ValueError("Pass the root .tex file explicitly for this directory")
            chosen = candidates[0]
        return chosen
    if not path.is_file():
        raise ValueError(f"Input file does not exist: {path}")
    return path


def read_manuscript(path):
    path = Path(path)
    sources = {}
    def expand(current, stack=()):
        current = current.resolve()
        if current in stack or len(stack) >= 20:
            raise ValueError(f"Circular or excessively nested manuscript include: {current}")
        text = current.read_text(encoding="utf-8-sig")
        sources[str(current)] = hashlib.sha256(current.read_bytes()).hexdigest()
        pattern = re.compile(r"(?<!\\)\\(?:input|include)\{([^}]+)\}")
        def include(match):
            target = current.parent / match[1].strip()
            if not target.suffix:
                target = target.with_suffix(".tex")
            return expand(target, stack + (current,))
        lines = [line.split("%", 1)[0] if not re.search(r"\\%", line) else line for line in text.splitlines()]
        return pattern.sub(include, "\n".join(lines))
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        import pymupdf
        with pymupdf.open(path) as doc:
            text = "\n\n".join(f"<!-- page {i+1} -->\n{page.get_text(sort=True)}" for i, page in enumerate(doc))
    elif suffix == ".tex":
        text = expand(path)
    elif suffix in (".md", ".markdown", ".txt"):
        text = path.read_text(encoding="utf-8-sig")
    else:
        raise ValueError("Supported inputs: PDF, LaTeX, Markdown or plain text")
    sources[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not text.strip():
        raise ValueError("No readable manuscript text; obtain a readable/OCR version before initialization")
    return text, sources


def append_history(output, event):
    path = Path(output) / "inputs" / "revisions.jsonl"
    path.parent.mkdir(exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"recorded_at": utc_now(), **event}, ensure_ascii=False) + "\n")


def render_steps(output):
    path = Path(output) / STEPS_FILE
    if not path.exists():
        return
    steps = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    parts = ["# Investigation steps", "", "Agent-reported actions; raw host tool events are separate provenance.", ""]
    for step in steps:
        parts += [f"## Step {step['step']}: {step['target']}", "",
                  "**Why now:** " + step["why"], "", "**Action:** " + step["action"], "",
                  "**Found:** " + step["found"], ""]
        if step.get("ops"):
            parts += ["**Operations:** " + "; ".join(step["ops"]), ""]
    (Path(output) / STEPS_MD).write_text("\n".join(parts), encoding="utf-8")
