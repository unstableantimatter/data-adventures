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
git clone git@github.com:unstableantimatter/data-adventures.git
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

## Publishing dashboards

Finished dashboards are published to [GitHub Pages](https://unstableantimatter.github.io/data-adventures/)
via the `docs/` folder. A landing page auto-generates from each project's `config.yaml`.

### Publish workflow

```bash
# 1. Generate (or regenerate) a project's dashboard
python projects/generation-priced-out/generate_dashboard.py

# 2. Collect all dashboards into docs/ and rebuild the landing page
python pipeline/publish.py

# 3. Commit and push
git add -A && git commit -m "Publish updated dashboards" && git push
```

GitHub Pages serves from `docs/` on `main` — no CI/CD workflow needed.
Each dashboard is available at `https://unstableantimatter.github.io/data-adventures/<project-slug>/`.

### What `publish.py` does

1. Scans `projects/*/reports/dashboard.html` for all projects that have a
   generated dashboard
2. Copies each into `docs/<project-slug>/index.html`
3. Reads each project's `config.yaml` for title and narrative hypothesis
4. Generates `docs/index.html` — a landing page with cards linking to every
   published dashboard

### Custom domain

To use a custom domain instead of the `github.io` URL:

1. Add a CNAME DNS record pointing to `unstableantimatter.github.io`
2. Run: `gh api repos/unstableantimatter/data-adventures/pages -X PUT -f "cname=yourdomain.com"`
3. Add a `docs/CNAME` file containing the bare domain (e.g. `yourdomain.com`)

### Adding a new dashboard to the site

No configuration needed. If a project has both `config.yaml` and
`reports/dashboard.html`, `publish.py` will pick it up automatically.
The landing page card text comes from `title` and `narrative_hypothesis`
in `config.yaml`.

## Directory structure

```
data-adventures/
├── pipeline/               # Reusable pipeline code
│   ├── config.py           # Project config loader
│   ├── publish.py          # Dashboard → docs/ publisher
│   └── templates/          # Notebook & design templates
├── projects/               # Research projects (isolated)
│   ├── generation-priced-out/
│   ├── deaths-of-despair/
│   └── qol-immigration/
├── docs/                   # GitHub Pages site (auto-generated)
│   ├── index.html          # Landing page
│   ├── generation-priced-out/index.html
│   └── deaths-of-despair/index.html
├── run.py                  # Single entrypoint
├── requirements.txt        # Python dependencies
├── backlog.md              # Pipeline backlog + project queue
└── README.md               # This file
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

| Project | Status | Live Dashboard |
|---------|--------|----------------|
| Generation Priced Out | Published | [View](https://unstableantimatter.github.io/data-adventures/generation-priced-out/) |
| Deaths of Despair | Published | [View](https://unstableantimatter.github.io/data-adventures/deaths-of-despair/) |
| Quality of Life vs. Immigration | Planned | `projects/qol-immigration/` |
