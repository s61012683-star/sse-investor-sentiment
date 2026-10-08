from __future__ import annotations

import argparse
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Iterable

from zhipuai import ZhipuAI

LOGGER = logging.getLogger("sentiment")

SYSTEM_PROMPT = (
    "你是一个金融学专家，请给出下面股吧帖子的情绪。"
    "若它是积极的则输出“1”，消极的输出“-1”，中立的输出“0”，"
    "只能输出以上三个数字。"
)


def get_client(api_key_env: str) -> ZhipuAI:
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise RuntimeError(
            f"Missing API key. Set the {api_key_env} environment variable first."
        )
    return ZhipuAI(api_key=api_key)


def parse_label(raw_label: str) -> int:
    label = raw_label.strip()
    if label in {"1", "-1", "0"}:
        return int(label)
    raise ValueError(f"Unexpected sentiment label: {raw_label!r}")


def classify(
    client: ZhipuAI,
    text: str,
    model: str,
    retries: int,
) -> int:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
            )
            return parse_label(response.choices[0].message.content)
        except Exception as error:  # The SDK exposes several transport/API errors.
            last_error = error
            if attempt >= retries:
                break
            time.sleep((2**attempt) + random.uniform(0.0, 0.5))
    raise RuntimeError("Sentiment classification failed after retries") from last_error


def iter_posts(path: Path) -> Iterable[dict]:
    with path.open(encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            if "date" not in item or "text" not in item:
                raise ValueError(f"Missing date/text fields on line {line_number}")
            yield item


def label_posts(
    input_path: Path,
    output_path: Path,
    model: str,
    api_key_env: str,
    retries: int,
    delay_seconds: float,
) -> int:
    client = get_client(api_key_env=api_key_env)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with output_path.open("w", encoding="utf-8") as output_file:
        for post in iter_posts(input_path):
            label = classify(
                client=client,
                text=post["text"],
                model=model,
                retries=retries,
            )
            result = {**post, "sentiment": label}
            output_file.write(json.dumps(result, ensure_ascii=False) + "\n")
            output_file.flush()
            count += 1
            if count % 100 == 0:
                LOGGER.info("Classified %s posts", count)
            time.sleep(delay_seconds)

    return count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Classify post sentiment with GLM.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/labeled_posts.jsonl"))
    parser.add_argument("--model", default=os.getenv("ZHIPUAI_MODEL", "glm-4-flash"))
    parser.add_argument("--api-key-env", default="ZHIPUAI_API_KEY")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    count = label_posts(
        input_path=args.input,
        output_path=args.output,
        model=args.model,
        api_key_env=args.api_key_env,
        retries=args.retries,
        delay_seconds=args.delay,
    )
    LOGGER.info("Saved %s labeled posts to %s", count, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
