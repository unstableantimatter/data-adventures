# Infrastructure

## Tech stack

| Layer | Choice | Why |
|-------|--------|-----|
| **Language** | Python 3.10–3.12 (3.11+ recommended) | All stack deps support 3.10+; 3.11+ for performance and native type syntax |
| **Environment** | venv + requirements.txt | Simple, reproducible, no extra tooling |
| **Data storage** | Local files: `data/raw/` (CSV/JSON), `data/processed/` (Parquet) | Reproducible, lightweight, versionable |
| **Data processing** | pandas, polars (optional) | Mature, well-documented |
| **Statistical analysis** | scipy, statsmodels | Correlation tests, regression, time series |
| **Changepoint detection** | ruptures | Lightweight, well-maintained |
| **Clustering / outliers** | scikit-learn | Standard toolkit |
| **Charts** | Plotly | Interactive, HTML-embeddable, shareable |
| **Notebooks** | Jupyter | Analysis + report in one artifact; Colab-compatible |
| **Notebook execution** | nbconvert (`--execute --to html`) | Built-in, headless execution + export |
| **Orchestration** | `run.py` — single entrypoint | One command per project |
| **LLM orchestration** | Cursor IDE | All LLM calls run through Cursor sessions using available models per phase |
| **LLM models** | Perplexity (research), Claude (code/narrative), Claude thinking / o3 / Gemini 2.5 Pro (deep analysis), GPT-4o (narrative/writing) | Best model per task; see `docs/llm_integration.md` |

## Python version compatibility

The pipeline and all dependencies in `requirements.txt` have been checked against PyPI metadata. Summary:

| Package | Tested version | Requires Python | Notes |
|---------|----------------|-----------------|--------|
| pandas | 2.3.3 | ≥3.9 | 3.10+ keeps upgrade path (pandas 3.0 will drop 3.10) |
| pyarrow | 18–21 | ≥3.9 | 3.9+ OK for current; 3.10+ for latest |
| openpyxl | 3.1.5 | ≥3.8 | No constraint |
| scipy | 1.13.1 (installed) | ≥3.9 | **1.14+ requires ≥3.10** — upgrading scipy later needs 3.10+ |
| statsmodels | 0.14.x | ≥3.9 | No constraint |
| ruptures | 1.1.10 | ≥3.9, &lt;3.14 | No constraint |
| scikit-learn | 1.5–1.6 | ≥3.9 | Latest 1.8+ may require 3.11+ |
| plotly | 5.24 / 6.x | ≥3.8 | No constraint |
| jupyter | 1.x | (meta-package) | Follows nbconvert/jupyter-core |
| nbconvert | 7.16+ | ≥3.8 | No constraint |
| pyyaml | 6.0.x | ≥3.8 | Use 6.0.1+ for 3.11+ |

**Conclusion**

- **Python 3.9** — Works with the **currently installed** versions (scipy 1.13.1, scikit-learn 1.6.1, etc.). Newer scipy (1.14+) and numpy 2.2+ require 3.10+, so staying on 3.9 will block some future upgrades. The codebase uses `from __future__ import annotations` so that `X | None`-style types work on 3.9.
- **Python 3.10** — **Minimum recommended.** Unblocks scipy/numpy upgrades, allows native `X | None` union syntax, supported by all listed packages.
- **Python 3.11** — **Recommended.** Same as 3.10 plus faster interpreter; fully supported by the stack.
- **Python 3.12** — Supported by pandas 2.3, scipy 1.14, numpy 2.x, and the rest of the stack.
- **Python 3.13+** — Not yet in the support matrix of all packages (e.g. pandas 2.3 classifiers list only 3.10–3.12). Prefer 3.10–3.12 for now.

**Recommended:** Use **Python 3.10, 3.11, or 3.12**. Prefer **3.11** for performance and long support. Create the venv with that interpreter (e.g. `python3.11 -m venv .venv`). If you use pyenv, add a `.python-version` file with `3.11` or `3.12`.

## Directory layout

```
data-adventures/
├── pipeline/                        # Reusable pipeline code (shared across all projects)
│   ├── ingest.py                    # Generic ingest logic
│   ├── clean.py                     # Generic clean/transform logic
│   ├── merge.py                     # Generic merge logic
│   ├── analyze.py                   # Layer 1 descriptive pass + Layer 2 flagging
│   ├── execute.py                   # Run notebooks + export HTML via nbconvert
│   └── templates/                   # Starter notebook templates
│       ├── 01_descriptive.ipynb     # Layer 1 template
│       ├── 02_findings.ipynb        # Layer 2 findings summary template
│       └── 03_story.ipynb           # Final story template
├── projects/                        # All research projects (isolated)
│   └── <project-name>/             # One project instance
│       ├── config.yaml              # Project config (name, hypothesis, indicators, hypotheses, sources)
│       ├── data/
│       │   ├── raw/                 # Immutable source files
│       │   └── processed/           # Cleaned Parquet files (generated)
│       ├── notebooks/               # Analysis notebooks (generated from templates + custom)
│       ├── reports/                 # Generated HTML, social content (generated)
│       └── README.md                # Project-specific notes
├── docs/                            # Pipeline-level documentation
│   ├── BRD.md
│   ├── infrastructure.md            # This file
│   ├── analytical_framework.md
│   ├── llm_integration.md
│   ├── agentic_hierarchy.md
│   ├── decisions.md
│   └── data_catalog.md
├── run.py                           # Single entrypoint: python run.py <project-name>
├── requirements.txt                 # Pinned Python dependencies
├── backlog.md                       # Pipeline backlog + project queue
└── README.md                        # Quick start
```

## Isolation rules

1. **Everything under `projects/<name>/` is self-contained.** Data, notebooks, and reports never reference files outside their project directory.
2. **Pipeline code in `pipeline/` is shared and stateless.** It reads a project's `config.yaml` and operates only within that project's directory tree.
3. **No cross-project data access.** A script running for project A must not read or write anything in project B's directory. (Exception: the future Cross-Study Analyst Agent, which will have explicit read-only access across projects — see `docs/agentic_hierarchy.md`.)
4. **`data/raw/` is immutable.** Once a file is placed in `data/raw/`, it is never modified. All transformations write to `data/processed/`.
5. **Generated artifacts are re-creatable.** Everything in `data/processed/`, `notebooks/` (executed state), and `reports/` can be regenerated by running the pipeline. These directories can be `.gitignored` if data is large.

## Pipeline flow

```
python run.py <project-name>
```

1. **Data stage:** Runs `pipeline/ingest.py`, `pipeline/clean.py`, `pipeline/merge.py` scoped to the project. Reads from `projects/<name>/data/raw/`, writes to `projects/<name>/data/processed/`.
2. **Analysis stage:** Executes notebooks in `projects/<name>/notebooks/` in order via nbconvert. Notebooks read from `data/processed/`.
3. **Export stage:** Converts executed notebooks to HTML via nbconvert. Writes to `projects/<name>/reports/`.

LLM assistance happens at each stage via Cursor sessions (see `docs/llm_integration.md`).

## How to run (quick reference)

```bash
# Clone and set up environment
git clone <repo-url>
cd data-adventures
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the full pipeline for a project
python run.py qol-immigration

# Or run individual stages
python run.py qol-immigration --stage data
python run.py qol-immigration --stage analyze
python run.py qol-immigration --stage export
```
