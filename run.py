#!/usr/bin/env python3
"""CLI entrypoint for the Vina docking pipeline."""

import argparse
import sys

from vinadock.config import Config, load_env_file
from vinadock.pipeline import run_all


def main():
    parser = argparse.ArgumentParser(
        description="AutoDock Vina re-docking pipeline",
    )
    parser.add_argument(
        "--config", metavar="FILE",
        help="Path to .env config file (default: config.env)",
    )
    parser.add_argument(
        "--complexes-dir", metavar="DIR",
        help="Override VINADOCK_COMPLEXES_DIR",
    )
    parser.add_argument(
        "--output-dir", metavar="DIR",
        help="Override VINADOCK_OUTPUT_DIR",
    )
    parser.add_argument(
        "--no-skip", action="store_true",
        help="Re-run even if scores.csv already exists",
    )
    args = parser.parse_args()

    # Load .env file
    env_file = args.config or "config.env"
    try:
        load_env_file(env_file)
    except FileNotFoundError:
        if args.config:
            print(f"Error: config file not found: {env_file}", file=sys.stderr)
            sys.exit(1)
        # Default config.env is optional

    config = Config.from_env()

    # CLI overrides
    if args.complexes_dir:
        from pathlib import Path
        config.complexes_dir = Path(args.complexes_dir)
    if args.output_dir:
        from pathlib import Path
        config.output_dir = Path(args.output_dir)
    if args.no_skip:
        config.skip_existing = False

    try:
        run_all(config)
    except ValueError as e:
        print(f"Configuration error:\n{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
