from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class DailyCounts:
    total: int = 0
    positive: int = 0
    neutral: int = 0
    negative: int = 0

    def add(self, sentiment: int) -> None:
        self.total += 1
        if sentiment == 1:
            self.positive += 1
        elif sentiment == -1:
            self.negative += 1
        elif sentiment == 0:
            self.neutral += 1
        else:
            raise ValueError(f"Unsupported sentiment label: {sentiment}")

    def sentiment_index(self, formula: str) -> float:
        directional = self.positive + self.negative
        if directional == 0:
            return 0.0
        if formula == "ratio":
            return (self.positive - self.negative) / directional
        if formula == "log-ratio":
            return math.log((1 + self.positive) / (1 + self.negative))
        raise ValueError(f"Unsupported formula: {formula}")


def iter_labeled_posts(path: Path) -> Iterable[dict]:
    with path.open(encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            if "date" not in item or "sentiment" not in item:
                raise ValueError(
                    f"Missing date/sentiment fields on line {line_number}"
                )
            yield item


def calculate_daily_metrics(input_path: Path, formula: str) -> list[dict]:
    daily: dict[str, DailyCounts] = defaultdict(DailyCounts)
    for post in iter_labeled_posts(input_path):
        daily[str(post["date"])].add(int(post["sentiment"]))

    rows: list[dict] = []
    for day in sorted(daily):
        counts = daily[day]
        rows.append(
            {
                "date": day,
                "info_count": counts.total,
                "positive": counts.positive,
                "neutral": counts.neutral,
                "negative": counts.negative,
                "sentiment_index": counts.sentiment_index(formula),
            }
        )
    return rows


def write_metrics(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "date",
        "info_count",
        "positive",
        "neutral",
        "negative",
        "sentiment_index",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build daily information-volume and sentiment metrics."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/daily_metrics.csv"))
    parser.add_argument(
        "--formula",
        choices=("ratio", "log-ratio"),
        default="ratio",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = calculate_daily_metrics(input_path=args.input, formula=args.formula)
    write_metrics(rows=rows, output_path=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
