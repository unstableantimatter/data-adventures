"""Scaffold a new project or copy notebook templates into an existing project."""

import shutil
from pathlib import Path

from pipeline.config import PROJECTS_DIR, get_project_dir, get_notebooks_dir

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def init_project(project_name: str) -> Path:
    """Create a new project directory with the standard layout and templates."""
    project_dir = PROJECTS_DIR / project_name
    if project_dir.exists():
        raise FileExistsError(f"Project '{project_name}' already exists at {project_dir}")

    project_dir.mkdir(parents=True)
    (project_dir / "data" / "raw").mkdir(parents=True)
    (project_dir / "data" / "processed").mkdir(parents=True)
    (project_dir / "notebooks").mkdir()
    (project_dir / "reports").mkdir()

    _write_config_stub(project_dir, project_name)
    _write_project_readme(project_dir, project_name)
    copy_templates(project_name)

    print(f"  [scaffold] Created project '{project_name}' at {project_dir}")
    return project_dir


def copy_templates(project_name: str) -> list[Path]:
    """Copy notebook templates into a project's notebooks/ directory."""
    notebooks_dir = get_notebooks_dir({"_project_dir": get_project_dir(project_name)})
    templates = sorted(TEMPLATES_DIR.glob("*.ipynb"))
    copied = []

    for tpl in templates:
        dest = notebooks_dir / tpl.name
        if dest.exists():
            print(f"  [scaffold] Skipping {tpl.name} (already exists)")
            continue
        shutil.copy2(tpl, dest)
        copied.append(dest)
        print(f"  [scaffold] Copied {tpl.name} -> notebooks/")

    return copied


def _write_config_stub(project_dir: Path, project_name: str) -> None:
    config_path = project_dir / "config.yaml"
    config_path.write_text(f"""# Project configuration — {project_name}

name: {project_name}
title: "{project_name}"
status: planned

narrative_hypothesis: >
  (Describe the narrative hypothesis to test.)

indicators: []
hypotheses: []
data_sources: []
""")


def _write_project_readme(project_dir: Path, project_name: str) -> None:
    readme_path = project_dir / "README.md"
    readme_path.write_text(f"""# {project_name} — Project Notes

## Narrative hypothesis

(Describe the narrative hypothesis to test.)

## Status

**Phase:** Not started (planned)

## Data catalog

| Name | Category | Source URL | Description | Format | License | Time range | Geo | Direction | Tags | Script |
|------|----------|-----------|-------------|--------|---------|------------|-----|-----------|------|--------|
| — | — | — | — | — | — | — | — | — | — | — |

## Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| — | — | — |
""")
