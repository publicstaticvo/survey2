from __future__ import annotations

import io
import pickle
import re
import shutil
import sys
import tarfile
import traceback
import uuid
from pathlib import Path

from .content_walk import section_to_text
from .latex_parser import LatexPaperParser


def _safe_extract_tar_buffer(buffer: bytes, target_dir: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(buffer), mode="r:gz") as archive:
        target_root = target_dir.resolve()
        for member in archive.getmembers():
            member_path = (target_root / member.name).resolve()
            if target_root not in member_path.parents and member_path != target_root:
                raise RuntimeError(f"Unsafe tar member path: {member.name}")
        archive.extractall(target_root)


def parse_arxiv_source_buffer(buffer: bytes, arxiv_id: str, tmp_parent: str | None = None) -> dict:
    root = Path(tmp_parent) if tmp_parent else Path.cwd() / "triage_tmp" / "arxiv_source"
    root.mkdir(parents=True, exist_ok=True)
    source_dir = root / f"arxiv_{re.sub(r'[^0-9A-Za-z]+', '_', arxiv_id)}_{uuid.uuid4().hex}"
    source_dir.mkdir(parents=True, exist_ok=False)
    try:
        try:
            _safe_extract_tar_buffer(buffer, source_dir)
        except tarfile.TarError:
            if buffer[:5] == b"%PDF-":
                return {"result": None, "download_error": False, "parse_error": True, "message": "returned_pdf"}
            tex_path = source_dir / "source.tex"
            tex_path.write_bytes(buffer)
        parser = LatexPaperParser()
        tex_count = len([path for path in source_dir.rglob("*.tex") if path.is_file()])
        main_tex = parser._find_main_tex(source_dir)
        if not main_tex:
            return {"result": None, "download_error": False, "parse_error": True, "message": "no_tex"}
        print(f"Parsing TeX source main file {Path(main_tex).name} from {tex_count} TeX files", flush=True)
        paper = parser.parse(main_tex)
        if not paper:
            return {"result": None, "download_error": False, "parse_error": True, "message": "no_paper"}
        abstract = section_to_text(paper.abstract)
        print(f"Parsed TeX source. It has {len(paper.children)} sections.", flush=True)
        return {
            "result": {"full_content": paper, "abstract": abstract},
            "download_error": False,
            "parse_error": False,
        }
    finally:
        shutil.rmtree(source_dir, ignore_errors=True)


def main(argv: list[str]) -> int:
    if len(argv) not in {4, 5}:
        print("usage: arxiv_source_worker <input-bytes> <output-pickle> <arxiv-id> [tmp-parent]", file=sys.stderr)
        return 2
    input_path = Path(argv[1])
    output_path = Path(argv[2])
    arxiv_id = argv[3]
    tmp_parent = argv[4] if len(argv) == 5 and argv[4] else None
    try:
        result = parse_arxiv_source_buffer(
            input_path.read_bytes(),
            arxiv_id,
            tmp_parent,
        )
    except BaseException as exc:
        result = {
            "result": None,
            "download_error": False,
            "parse_error": True,
            "message": repr(exc),
            "traceback": traceback.format_exc(),
        }
    output_path.write_bytes(pickle.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
