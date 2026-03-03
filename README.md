# Data Adventures

A reusable, LLM-assisted data study pipeline. Feed it a hypothesis and raw data;
get back interactive, shareable reports.

## How it works

Each research project gets its own isolated directory under `projects/`. The
pipeline automates the path from raw data to published HTML reports with
interactive Plotly charts, using LLM agents (via Cursor) at every phase.

**Pipeline phases (per project):**

1. **Find** — discover and evaluate data sources (research LLM)
2. **Study & coalesce** — ingest, clean, merge into Parquet (code LLM)
3. **Analyze** — three-layer framework: descriptive pass, flagging, deep-dives (deep-thinking LLMs)
4. **Design the story** — narrative arc, chart specs, sequencing (narrative LLM)
5. **Execute & share** — build notebooks, export HTML, generate social content (writing LLM)

## Quick start

```bash
# Clone and set up
git clone <repo-url>
cd data-adventures
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the full pipeline for a project
python run.py qol-immigration

# Run a specific stage
python run.py qol-immigration --stage data
python run.py qol-immigration --stage analyze
python run.py qol-immigration --stage export
```

## Creating a new project

1. Create a directory under `projects/`:
   ```
   projects/my-new-study/
   ├── config.yaml
   ├── data/raw/
   ├── data/processed/
   ├── notebooks/
   ├── reports/
   └── README.md
   ```
2. Populate `config.yaml` with: project name, narrative hypothesis, indicator
   definitions, and hypothesis definitions. See
   `projects/qol-immigration/config.yaml` for an example.
3. Run the pipeline: `python run.py my-new-study`

## Directory structure

```
data-adventures/
├── pipeline/           # Reusable pipeline code
│   └── templates/      # Notebook templates
├── projects/           # Research projects (isolated)
│   └── qol-immigration/
├── docs/               # Pipeline documentation
├── run.py              # Single entrypoint
├── requirements.txt    # Python dependencies
├── backlog.md          # Pipeline backlog + project queue
└── README.md           # This file
```

## Documentation

| Document | What it covers |
|----------|---------------|
| [backlog.md](backlog.md) | Pipeline backlog, project queue, future items |
| [docs/BRD.md](docs/BRD.md) | Business requirements, acceptance criteria, scope |
| [docs/infrastructure.md](docs/infrastructure.md) | Tech stack, directory layout, isolation rules |
| [docs/analytical_framework.md](docs/analytical_framework.md) | Three analysis layers, indicator schema, hypothesis patterns |
| [docs/llm_integration.md](docs/llm_integration.md) | LLM roles per phase, model recommendations, guardrails |
| [docs/agentic_hierarchy.md](docs/agentic_hierarchy.md) | Who does what — human, AI agent, future cross-study agent |
| [docs/decisions.md](docs/decisions.md) | Decision log with dates and rationale |
| [docs/data_catalog.md](docs/data_catalog.md) | Data catalog template for per-project use |
| [docs/docs_review_checklist.md](docs/docs_review_checklist.md) | Periodic docs health check — structure, cross-reference, and semantic checks |

## Current projects

| Project | Status | Directory |
|---------|--------|-----------|
| Quality of Life in the USA vs. Immigration Trends | Planned | `projects/qol-immigration/` |
