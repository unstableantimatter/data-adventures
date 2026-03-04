#!/usr/bin/env python3
"""Data Adventures — pipeline entrypoint.

Usage:
    python run.py <project-name>                     # run all stages
    python run.py <project-name> --stage data        # ingest + clean + merge only
    python run.py <project-name> --stage analyze     # execute notebooks only
    python run.py <project-name> --stage export      # export notebooks to HTML only
    python run.py <project-name> --init              # create a new project with templates
    python run.py <project-name> --copy-templates    # copy notebook templates into existing project
"""

import argparse
import sys

from pipeline.config import load_config
from pipeline import ingest, clean, merge, execute


STAGES = ("data", "analyze", "export")


def run_data(config: dict) -> None:
    print("\n=== Stage: Data (ingest -> clean -> merge) ===\n")
    ingest.run(config)
    clean.run(config)
    merge.run(config)


def run_analyze(config: dict) -> None:
    print("\n=== Stage: Analyze (execute notebooks) ===\n")
    execute.run_notebooks(config)


def run_export(config: dict) -> None:
    print("\n=== Stage: Export (notebooks -> HTML) ===\n")
    execute.export_html(config)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Data Adventures pipeline for a project."
    )
    parser.add_argument(
        "project",
        help="Project name (directory name under projects/)",
    )
    parser.add_argument(
        "--stage",
        choices=STAGES,
        default=None,
        help="Run a specific stage only. Omit to run all stages in order.",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Create a new project with standard layout and notebook templates.",
    )
    parser.add_argument(
        "--copy-templates",
        action="store_true",
        help="Copy notebook templates into an existing project's notebooks/ directory.",
    )
    args = parser.parse_args()

    if args.init:
        from pipeline.scaffold import init_project
        try:
            init_project(args.project)
        except FileExistsError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        print("\nDone.")
        return

    if args.copy_templates:
        from pipeline.scaffold import copy_templates
        try:
            copy_templates(args.project)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        print("\nDone.")
        return

    try:
        config = load_config(args.project)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Pipeline: {config.get('title', args.project)}")
    print(f"Project dir: {config['_project_dir']}")

    if args.stage is None:
        run_data(config)
        run_analyze(config)
        run_export(config)
    elif args.stage == "data":
        run_data(config)
    elif args.stage == "analyze":
        run_analyze(config)
    elif args.stage == "export":
        run_export(config)

    print("\nDone.")


if __name__ == "__main__":
    main()
