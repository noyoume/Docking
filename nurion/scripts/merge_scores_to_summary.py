#!/usr/bin/env python3
"""Rebuild global summary.csv from per-complex scores.csv files."""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vinadock.scoring import load_scores_csv
from vinadock.summary import write_summary


def main():
    parser = argparse.ArgumentParser(description="Merge scores.csv files into one summary.csv")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    all_results = {}
    for scores_csv in sorted(args.output_dir.rglob("scores.csv")):
        scores = load_scores_csv(scores_csv)
        if scores:
            all_results[scores_csv.parent.name] = scores

    summary_path = args.output_dir / "summary.csv"
    rows = write_summary(all_results, summary_path)
    print(f"Wrote {len(rows)} summary rows to {summary_path}")


if __name__ == "__main__":
    main()
