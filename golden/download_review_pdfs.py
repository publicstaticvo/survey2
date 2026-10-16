"""Download the exact review-version PDFs referenced by the golden dataset.

The downloader deliberately does not search by title, query arXiv, or use any
fallback source. Every downloaded PDF must come from the paper_url field of
the corresponding record in golden/data.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import hashlib
import http.client
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


EXCLUDED_IDS = {"037", "138"}
ALLOWED_HOSTS = {"openreview.net", "www.openreview.net"}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0 Safari/537.36 SurveyAudit-PDF-Downloader/1.0"
)


@dataclass
class DownloadRecord:
    paper_id: str
    split: str
    record_file: str
    output_file: str
    paper_title: str
    source_url: str
    status: str
    byte_count: int = 0
    sha256: str = ""
    error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download review-version PDFs explicitly listed in golden/data."
    )
    root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "data",
    )
    parser.add_argument(
        "--testset-dir",
        type=Path,
        default=root / "triage" / "test_inputs" / "human_testset",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "review_pdfs",
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--audit-only",
        action="store_true",
        help="Rebuild the manifest from existing PDFs without network access.",
    )
    parser.add_argument(
        "--credentials-file",
        type=Path,
        default=Path(__file__).resolve().parent / "parse_golden_paper_content.py",
        help="Local Python file containing OPENREVIEW_ID and OPENREVIEW_PASSWORD.",
    )
    return parser.parse_args()


def paper_id(path: Path) -> str:
    prefix = path.name.split("_", 1)[0]
    if len(prefix) != 3 or not prefix.isdigit():
        raise ValueError(f"Record filename does not start with a three-digit ID: {path.name}")
    return prefix


def record_paths(data_dir: Path) -> list[Path]:
    records = [
        path
        for path in sorted(data_dir.glob("*.json"))
        if not path.name.startswith("_") and paper_id(path) not in EXCLUDED_IDS
    ]
    if len(records) != 168:
        raise RuntimeError(
            f"Expected 168 downloadable records after excluding 037 and 138; "
            f"found {len(records)} in {data_dir}"
        )
    return records


def testset_names(testset_dir: Path) -> set[str]:
    names = {
        path.name
        for path in testset_dir.glob("*.json")
        if path.name[:3].isdigit() and path.name.count(".") == 1
    }
    if len(names) != 50:
        raise RuntimeError(
            f"Expected 50 dataset records in human_testset; found {len(names)} "
            f"in {testset_dir}"
        )
    return names


def validate_source_url(url: str, record_file: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(
            f"{record_file}: paper_url is not an allowed OpenReview HTTPS URL: {url}"
        )
    allowed_path = parsed.path.startswith(("/pdf/", "/attachment/"))
    if not allowed_path or not parsed.path.endswith(".pdf"):
        raise ValueError(
            f"{record_file}: paper_url is not an explicit OpenReview PDF URL: {url}"
        )


def is_pdf(data: bytes) -> bool:
    return data.startswith(b"%PDF-") and b"%%EOF" in data[-4096:]


def existing_pdf(path: Path) -> tuple[int, str] | None:
    if not path.is_file():
        return None
    data = path.read_bytes()
    if not is_pdf(data):
        return None
    return len(data), hashlib.sha256(data).hexdigest()


def load_credentials(path: Path) -> tuple[str, str]:
    values = {
        "OPENREVIEW_ID": os.environ.get("OPENREVIEW_ID", ""),
        "OPENREVIEW_PASSWORD": os.environ.get("OPENREVIEW_PASSWORD", ""),
    }
    if all(values.values()):
        print("load credentials from env")
        return values["OPENREVIEW_ID"], values["OPENREVIEW_PASSWORD"]
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id in values:
            value = ast.literal_eval(node.value)
            if isinstance(value, str):
                values[target.id] = value
    if not all(values.values()):
        raise RuntimeError(
            "OpenReview credentials were not found in the environment or credentials file"
        )
    return values["OPENREVIEW_ID"], values["OPENREVIEW_PASSWORD"]


def openreview_token(
    opener: urllib.request.OpenerDirector,
    credentials: tuple[str, str],
    timeout: float,
    retries: int,
) -> str:
    user_id, password = credentials
    print("logging in")
    body = json.dumps({"id": user_id, "password": password}).encode("utf-8")
    request = urllib.request.Request(
        "https://api2.openreview.net/login",
        data=body,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with opener.open(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            token = payload.get("token")
            if not isinstance(token, str) or not token:
                raise RuntimeError(
                    "OpenReview login succeeded without returning an access token"
                )
            return token
        except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(f"OpenReview login failed after {retries} attempts: {last_error}")


def fetch_pdf(
    url: str,
    token: str,
    timeout: float,
    retries: int,
) -> bytes:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf",
            "Authorization": f"Bearer {token}",
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with opener.open(request, timeout=timeout) as response:
                data = response.read()
            if not is_pdf(data):
                raise ValueError("response is not a complete PDF")
            return data
        except (
            urllib.error.URLError,
            TimeoutError,
            ValueError,
            http.client.IncompleteRead,
            http.client.RemoteDisconnected,
            ConnectionResetError,
        ) as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError) and 400 <= exc.code < 500:
                break
            if attempt < retries:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(f"download failed after {retries} attempts: {last_error}")


def write_pdf_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def write_manifest(output_dir: Path, records: Iterable[DownloadRecord]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "download_manifest.jsonl"
    temporary = manifest_path.with_suffix(".jsonl.part")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
    os.replace(temporary, manifest_path)


def download_one(
    record_path: Path,
    tests: set[str],
    args: argparse.Namespace,
    token: str,
) -> DownloadRecord:
    pid = paper_id(record_path)
    split = "human_testset" if record_path.name in tests else "development_set"
    output_path = args.output_dir / split / f"{record_path.stem}.pdf"
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    source_url = payload.get("paper_url")
    if not isinstance(source_url, str) or not source_url.strip():
        raise ValueError(f"{record_path.name}: missing paper_url")
    source_url = source_url.strip()
    validate_source_url(source_url, record_path.name)

    result = DownloadRecord(
        paper_id=pid,
        split=split,
        record_file=record_path.name,
        output_file=str(output_path.resolve()),
        paper_title=str(payload.get("paper_title", "")),
        source_url=source_url,
        status="pending",
    )
    try:
        cached = None if args.force else existing_pdf(output_path)
        if cached is not None:
            result.byte_count, result.sha256 = cached
            result.status = "existing"
        elif args.audit_only:
            result.status = "failed"
            result.error = "PDF unavailable from the dataset-provided URL after download attempts"
        else:
            data = fetch_pdf(source_url, token, args.timeout, args.retries)
            write_pdf_atomic(output_path, data)
            result.byte_count = len(data)
            result.sha256 = hashlib.sha256(data).hexdigest()
            result.status = "downloaded"
    except Exception as exc:  # Keep the full batch auditable and resumable.
        result.status = "failed"
        result.error = f"{type(exc).__name__}: {exc}"
    if args.delay > 0:
        time.sleep(args.delay)
    return result


def main() -> int:
    args = parse_args()
    records = record_paths(args.data_dir)
    tests = testset_names(args.testset_dir)
    token = ""
    if not args.audit_only:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        token = openreview_token(
            opener,
            load_credentials(args.credentials_file),
            args.timeout,
            args.retries,
        )
    results: list[DownloadRecord] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(download_one, path, tests, args, token): path
            for path in records
        }
        for completed, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            result = future.result()
            results.append(result)
            results.sort(key=lambda item: item.paper_id)
            write_manifest(args.output_dir, results)
            print(
                f"[{completed:03d}/{len(records)}] {result.paper_id} "
                f"{result.split:<15} {result.status}",
                flush=True,
            )

    split_counts = {
        split: sum(1 for result in results if result.split == split)
        for split in ("human_testset", "development_set")
    }
    failed = [result for result in results if result.status == "failed"]
    print(
        "Summary: "
        f"human_testset={split_counts['human_testset']}, "
        f"development_set={split_counts['development_set']}, "
        f"failed={len(failed)}"
    )
    if split_counts != {"human_testset": 50, "development_set": 118}:
        raise RuntimeError(f"Unexpected split counts: {split_counts}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
