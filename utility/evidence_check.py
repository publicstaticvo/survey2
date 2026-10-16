from __future__ import annotations

import html
import re
import unicodedata
from difflib import SequenceMatcher

from .tool_config import ToolConfig


class EvidenceCheck:
    def __init__(self, config: ToolConfig):
        self._mean_cov_weight = config.mean_cov_weight
        self._non_compat_punishment = config.non_compat_punishment
        self._confidence_threshold = config.confidence_threshold
        self._fuzzy_min_token_length = config.evidence_fuzzy_min_token_length
        self._ordered_min_matched_tokens = config.evidence_ordered_min_matched_tokens
        self._token_similarity_threshold = config.evidence_token_similarity_threshold
        self._ordered_token_coverage_threshold = config.evidence_ordered_token_coverage_threshold
        self._enabled = getattr(config, "evidence_source_verification", True)

    def _normalize_text(self, sequence: str) -> str:
        text = unicodedata.normalize("NFKC", str(sequence or ""))
        text = html.unescape(text)
        text = text.replace("\\n", " ").replace("\\r", " ").replace("\\t", " ")
        text = re.sub(r"\\([a-zA-Z]+)\b", r"\1", text)
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        text = text.translate(str.maketrans({
            "\u2018": "'",
            "\u2019": "'",
            "\u201b": "'",
            "\u0060": "'",
            "\u00b4": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u201e": '"',
            "\u201f": '"',
            "\u00a0": " ",
            "\u2007": " ",
            "\u202f": " ",
            "\u00ad": "",
        }))
        text = "".join("-" if unicodedata.category(char) == "Pd" else char for char in text)
        text = re.sub(r"<\s*mask\s*>", " ", text, flags=re.IGNORECASE)
        # PDF line wrapping may split a word as ``trans-\nport``.
        text = re.sub(r"(?<=\w)-(?=\s*\w)", "", text)
        return re.sub(r"\s+", " ", text).strip().casefold()

    def _compact_text(self, sequence: str) -> str:
        return re.sub(r"[^0-9a-z]+", "", self._normalize_text(sequence))

    def _tokens(self, sequence: str) -> list[str]:
        return re.findall(r"[0-9a-z]+", self._normalize_text(sequence))

    def _split_evidence_items(self, quote: list[str]) -> list[str]:
        pieces: list[str] = []
        for item in quote:
            text = str(item or "").strip()
            if not text:
                continue
            parts = [part.strip() for part in re.split(r"\.{3,}", text) if part.strip()]
            pieces.extend(parts if parts else [text])
        return pieces

    def _split_sentences(self, sequence: str) -> list[str]:
        text = self._normalize_text(sequence)
        if not text:
            return []
        parts = re.split(r"(?<=[.!?])\s+|[\n\r]+", text)
        return [part.strip() for part in parts if part.strip()]

    def _ordered_token_match(self, piece: str, source_doc: str) -> bool:
        """Match mostly identical words while tolerating insertions and OCR errors."""
        evidence_tokens = self._tokens(piece)
        if len(evidence_tokens) < self._ordered_min_matched_tokens:
            return False

        source_sentences = self._split_sentences(source_doc) or [source_doc]
        for sentence in source_sentences:
            source_tokens = self._tokens(sentence)
            previous = [0] * (len(evidence_tokens) + 1)
            for source_token in source_tokens:
                current = [0]
                for evidence_index, evidence_token in enumerate(evidence_tokens, 1):
                    matched = previous[evidence_index]
                    if (
                        source_token == evidence_token
                        or (
                            len(source_token) >= self._fuzzy_min_token_length
                            and len(evidence_token) >= self._fuzzy_min_token_length
                            and SequenceMatcher(None, source_token, evidence_token).ratio() >= self._token_similarity_threshold
                        )
                    ):
                        matched = max(matched, previous[evidence_index - 1] + 1)
                    matched = max(matched, current[-1])
                    current.append(matched)
                previous = current

            matched_count = previous[-1]
            coverage = matched_count / len(evidence_tokens)
            if (
                matched_count >= self._ordered_min_matched_tokens
                and coverage >= self._ordered_token_coverage_threshold
            ):
                return True
        return False

    def _match_piece(self, piece: str, source_doc: str) -> bool:
        piece_text = self._normalize_text(piece)
        if not piece_text:
            return False
        source_text = self._normalize_text(source_doc)
        if not source_text:
            return False
        if piece_text in source_text:
            return True
        if any(piece_text == sentence for sentence in self._split_sentences(source_doc)):
            return True

        compact_piece = self._compact_text(piece)
        compact_source = self._compact_text(source_doc)
        if not compact_piece or not compact_source:
            return False
        if compact_piece in compact_source:
            return True

        source_sentences = [self._compact_text(sentence) for sentence in self._split_sentences(source_doc)]
        source_sentences = [sentence for sentence in source_sentences if sentence]
        if not source_sentences:
            source_sentences = [compact_source]

        length = len(compact_piece)
        threshold = 0.98 if length < 40 else 0.94 if length < 120 else 0.90
        if any(
            SequenceMatcher(None, compact_piece, sentence).ratio() >= threshold
            for sentence in source_sentences
        ):
            return True
        return self._ordered_token_match(piece, source_doc)

    def verify(self, quote: list[str], source_doc: str, min_char_len: int = 20) -> tuple[bool, float]:
        if not self._enabled:
            return True, 1.0

        anchors = [
            piece
            for piece in self._split_evidence_items(quote)
            if sum(len(ch) for ch in re.sub(r"\s+", "", piece)) >= min_char_len
        ]
        if not anchors:
            return False, 0.0

        matched = sum(1 for anchor in anchors if self._match_piece(anchor, source_doc))
        confidence = matched / len(anchors)
        return confidence >= self._confidence_threshold, confidence
