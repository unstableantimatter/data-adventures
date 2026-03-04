"""Load and validate project configuration from config.yaml."""

from pathlib import Path
from typing import Any

import yaml


PROJECTS_DIR = Path(__file__).resolve().parent.parent / "projects"


def get_project_dir(project_name: str) -> Path:
    project_dir = PROJECTS_DIR / project_name
    if not project_dir.is_dir():
        raise FileNotFoundError(
            f"Project '{project_name}' not found at {project_dir}"
        )
    return project_dir


def load_config(project_name: str) -> dict[str, Any]:
    project_dir = get_project_dir(project_name)
    config_path = project_dir / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"No config.yaml found for project '{project_name}' at {config_path}"
        )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    config.setdefault("indicators", [])
    config.setdefault("hypotheses", [])
    config.setdefault("data_sources", [])
    config["_project_dir"] = project_dir
    return config


def get_data_raw_dir(config: dict) -> Path:
    return config["_project_dir"] / "data" / "raw"


def get_data_processed_dir(config: dict) -> Path:
    return config["_project_dir"] / "data" / "processed"


def get_notebooks_dir(config: dict) -> Path:
    return config["_project_dir"] / "notebooks"


def get_reports_dir(config: dict) -> Path:
    return config["_project_dir"] / "reports"
