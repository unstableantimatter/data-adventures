"""Execute notebooks and export to HTML.

Runs Jupyter notebooks in a project's notebooks/ directory in alphabetical
order via nbconvert, then exports each to HTML in reports/.
"""

import os
import subprocess
import sys
from pathlib import Path

from pipeline.config import get_notebooks_dir, get_reports_dir

REPO_ROOT = Path(__file__).resolve().parent.parent


def _env_with_pythonpath() -> dict[str, str]:
    """Return a copy of os.environ with REPO_ROOT prepended to PYTHONPATH."""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{REPO_ROOT}{os.pathsep}{existing}" if existing else str(REPO_ROOT)
    return env


def run_notebooks(config: dict) -> list[Path]:
    """Execute all notebooks in order. Returns list of executed notebook paths."""
    notebooks_dir = get_notebooks_dir(config)
    notebooks = sorted(notebooks_dir.glob("*.ipynb"))

    if not notebooks:
        print("  [execute] No notebooks found to run.")
        return []

    env = _env_with_pythonpath()
    executed = []
    for nb in notebooks:
        print(f"  [execute] Running {nb.name}...")
        result = subprocess.run(
            [
                sys.executable, "-m", "jupyter", "nbconvert",
                "--to", "notebook",
                "--execute",
                "--inplace",
                "--ExecutePreprocessor.timeout=600",
                str(nb),
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            print(f"  [execute] FAILED: {nb.name}")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
        else:
            print(f"  [execute] OK: {nb.name}")
            executed.append(nb)

    return executed


def export_html(config: dict) -> list[Path]:
    """Export all notebooks to HTML in reports/. Returns list of HTML paths."""
    notebooks_dir = get_notebooks_dir(config)
    reports_dir = get_reports_dir(config)
    reports_dir.mkdir(parents=True, exist_ok=True)

    notebooks = sorted(notebooks_dir.glob("*.ipynb"))
    if not notebooks:
        print("  [export] No notebooks found to export.")
        return []

    env = _env_with_pythonpath()
    outputs = []
    for nb in notebooks:
        html_name = nb.stem + ".html"
        html_path = reports_dir / html_name
        print(f"  [export] {nb.name} -> {html_name}")
        result = subprocess.run(
            [
                sys.executable, "-m", "jupyter", "nbconvert",
                "--to", "html",
                "--no-input",
                f"--output-dir={reports_dir}",
                str(nb),
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            print(f"  [export] FAILED: {nb.name}")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
        else:
            outputs.append(html_path)

    print(f"  [export] {len(outputs)} HTML report(s) written to {reports_dir}")
    return outputs
