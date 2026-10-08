from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

import jieba

PUNCTUATION_RE = re.compile(r"[.【】0-9、—。，！~,*?;:()\[\]{}\"'“”‘’]+")


def iter_texts(path: Path, sentiment_filter: int | None) -> Iterable[str]:
    with path.open(encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            if "text" not in item:
                raise ValueError(f"Missing text field on line {line_number}")
            if sentiment_filter is not None and item.get("sentiment") != sentiment_filter:
                continue
            yield str(item["text"])


def count_words(
    input_path: Path,
    top_k: int,
    min_length: int,
    sentiment_filter: int | None,
) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for text in iter_texts(input_path=input_path, sentiment_filter=sentiment_filter):
        cleaned = PUNCTUATION_RE.sub("", text)
        counts.update(
            word
            for word in jieba.cut(cleaned)
            if len(word.strip()) >= min_length
        )
    return counts.most_common(top_k)


def write_keywords(rows: list[tuple[str, int]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["word", "count"])
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Count frequent words in posts.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/keywords.csv"))
    parser.add_argument("--top-k", type=int, default=100)
    parser.add_argument("--min-length", type=int, default=2)
    parser.add_argument("--sentiment", type=int, choices=(-1, 0, 1))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = count_words(
        input_path=args.input,
        top_k=args.top_k,
        min_length=args.min_length,
        sentiment_filter=args.sentiment,
    )
    write_keywords(rows=rows, output_path=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
