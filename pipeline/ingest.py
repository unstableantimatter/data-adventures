"""Ingest raw data files for a project.

Reads data_sources from config.yaml and ensures each source has corresponding
files in data/raw/. For v1 this is a manual step — the user places files in
data/raw/ and this module validates they exist.

Future: add download logic for URLs defined in data_sources.
"""

from pathlib import Path

from pipeline.config import get_data_raw_dir


def run(config: dict) -> list[Path]:
    """Validate that raw data files exist. Returns list of raw file paths."""
    raw_dir = get_data_raw_dir(config)
    raw_files = sorted(raw_dir.glob("*"))
    raw_files = [f for f in raw_files if f.name != ".gitkeep"]

    if not raw_files:
        print(f"  [ingest] No raw data files found in {raw_dir}")
        print(f"  [ingest] Place source files there and re-run.")
        return []

    print(f"  [ingest] Found {len(raw_files)} raw file(s):")
    for f in raw_files:
        print(f"    - {f.name} ({f.stat().st_size:,} bytes)")

    sources = config.get("data_sources", [])
    if sources:
        source_names = {s.get("name") for s in sources}
        print(f"  [ingest] Config declares {len(sources)} source(s): {source_names}")

    return raw_files
