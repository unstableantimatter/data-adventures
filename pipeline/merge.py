"""Merge processed Parquet files into a unified dataset.

If the project has a custom merge module at ``src/merge_data.py``, that
module's ``run(config)`` function is called instead of the generic fallback.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

from pipeline.config import get_data_processed_dir


def run(config: dict) -> dict[str, pd.DataFrame]:
    """Load/merge processed Parquet files. Returns dict of name → DataFrame."""
    project_dir = Path(config["_project_dir"])
    custom = project_dir / "src" / "merge_data.py"

    if custom.exists():
        print(f"  [merge] Using project-specific merger: {custom.relative_to(project_dir)}")
        spec = importlib.util.spec_from_file_location("merge_data", custom)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod.run(config)

    return _generic_run(config)


def _generic_run(config: dict) -> dict[str, pd.DataFrame]:
    """Fallback: load every Parquet file as-is."""
    processed_dir = get_data_processed_dir(config)
    parquet_files = sorted(processed_dir.glob("*.parquet"))

    if not parquet_files:
        print("  [merge] No processed Parquet files found.")
        return {}

    datasets = {}
    for pf in parquet_files:
        df = pd.read_parquet(pf)
        datasets[pf.stem] = df
        print(f"  [merge] Loaded {pf.stem}: {len(df):,} rows x {len(df.columns)} cols")

    print(f"  [merge] {len(datasets)} dataset(s) available for analysis.")
    return datasets
