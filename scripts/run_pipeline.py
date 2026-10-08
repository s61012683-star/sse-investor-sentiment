from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = {
    "crawl": "src.crawler",
    "sentiment": "src.sentiment",
    "metrics": "src.metrics",
    "keywords": "src.keywords",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one stage of the investor-sentiment pipeline."
    )
    parser.add_argument("stage", choices=MODULES)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = [sys.executable, "-m", MODULES[args.stage], *args.args]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
