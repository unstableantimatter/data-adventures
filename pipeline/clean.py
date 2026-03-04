"""Clean and transform raw data into processed Parquet files.

If the project has a custom cleaning module at ``src/clean_data.py``, that
module's ``run(config)`` function is called instead of the generic fallback.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

from pipeline.config import get_data_raw_dir, get_data_processed_dir


def run(config: dict) -> list[Path]:
    """Clean raw files and write to processed/. Returns list of output paths."""
    project_dir = Path(config["_project_dir"])
    custom = project_dir / "src" / "clean_data.py"

    if custom.exists():
        print(f"  [clean] Using project-specific cleaner: {custom.relative_to(project_dir)}")
        spec = importlib.util.spec_from_file_location("clean_data", custom)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod.run(config)

    return _generic_run(config)


def _generic_run(config: dict) -> list[Path]:
    """Fallback: read every raw file and dump to Parquet unchanged."""
    raw_dir = get_data_raw_dir(config)
    processed_dir = get_data_processed_dir(config)
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(raw_dir.glob("*"))
    raw_files = [f for f in raw_files if f.name != ".gitkeep"]

    if not raw_files:
        print("  [clean] No raw files to process.")
        return []

    outputs = []
    for raw_file in raw_files:
        try:
            df = _read_raw(raw_file)
        except ValueError as e:
            print(f"  [clean] Skipping {raw_file.name}: {e}")
            continue

        out_name = raw_file.stem + ".parquet"
        out_path = processed_dir / out_name
        df.to_parquet(out_path, index=False)
        outputs.append(out_path)
        print(f"  [clean] {raw_file.name} -> {out_name} ({len(df):,} rows, {len(df.columns)} cols)")

    return outputs


def _read_raw(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    elif suffix in (".xls", ".xlsx"):
        return pd.read_excel(path)
    elif suffix == ".json":
        return pd.read_json(path)
    elif suffix == ".parquet":
        return pd.read_parquet(path)
    elif suffix in (".tsv", ".tab"):
        return pd.read_csv(path, sep="\t")
    else:
        raise ValueError(f"Unsupported format: {suffix}")
