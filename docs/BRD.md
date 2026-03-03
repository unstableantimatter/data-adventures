# Business Requirements Document — Data Adventures Pipeline

## 1. Purpose

Build a reusable, LLM-assisted data study pipeline that takes a narrative
hypothesis and raw data sources and produces reproducible, interactive,
shareable reports (Jupyter notebooks exported to HTML). The pipeline is
designed to run many independent studies, each isolated in its own project
directory.

## 2. Scope

### In scope

- Multi-project architecture with full isolation (data, notebooks, reports per project).
- Five-phase process per project: Find, Study & coalesce, Analyze, Design the story, Execute & share.
- Three-layer analytical framework: automatic descriptive pass, flagging engine, directed deep-dives.
- Flexible indicator schema — new data categories and variables addable mid-study without restructuring.
- Custom hypothesis definitions — user-defined relationships tested via reusable narrative reframing patterns (masking, displacement, divergence, lag/lead, segmentation, threshold).
- LLM integration at every phase via Cursor (research, code reasoning, deep thinking, narrative, writing) with human-in-the-loop guardrails.
- Interactive Plotly charts embedded in Jupyter notebooks.
- Automated notebook execution and HTML export via nbconvert.
- Single entrypoint (`run.py`) for the data-to-report pipeline.

### Out of scope (v1)

- Custom web application or dashboard framework.
- PySpark / distributed compute (add only if data outgrows single machine).
- Causal inference methodology (journalistic / exploratory rigor for v1).
- Automated publishing to social media (manual posting from generated content).
- Cross-study analysis agent (deferred until 3–4 studies complete).

## 3. Deliverables

Per project:

| Deliverable | Format | Location |
|-------------|--------|----------|
| Processed dataset | Parquet files | `projects/<name>/data/processed/` |
| Descriptive report (Layer 1) | Jupyter notebook + HTML | `projects/<name>/notebooks/`, `projects/<name>/reports/` |
| Findings summary (Layer 2) | Markdown or notebook | `projects/<name>/notebooks/` |
| Deep-dive reports (Layer 3) | Jupyter notebooks + HTML | `projects/<name>/notebooks/`, `projects/<name>/reports/` |
| Story report (final) | Jupyter notebook + HTML | `projects/<name>/notebooks/`, `projects/<name>/reports/` |
| Social-ready content | Text drafts | `projects/<name>/reports/` |

Pipeline-level:

| Deliverable | Format | Location |
|-------------|--------|----------|
| Pipeline code | Python scripts | `pipeline/` |
| Notebook templates | `.ipynb` | `pipeline/templates/` |
| Documentation suite | Markdown | `docs/` |

## 4. Acceptance criteria by phase

### Phase 1: Find

- [ ] Research LLM has been used to identify candidate data sources.
- [ ] Each source is documented in the project's data catalog (name, URL, format, license, time range, geographic granularity).
- [ ] Human has reviewed and approved the source list.
- [ ] `config.yaml` indicators section is populated with at least the initial set.

### Phase 2: Study & coalesce

- [ ] Ingest scripts exist in `pipeline/` or project-specific overrides.
- [ ] Raw data is stored in `projects/<name>/data/raw/` (immutable).
- [ ] Cleaning and merge logic has been reviewed (LLM-assisted schema analysis).
- [ ] Processed data is in `projects/<name>/data/processed/` as Parquet.
- [ ] Data catalog is updated with actual schemas and row counts.

### Phase 3: Analyze

- [ ] Layer 1 descriptive pass has run — notebook with univariate profiles, trends, correlations, changepoints, geographic variation.
- [ ] Layer 2 flagging engine has run — findings summary with ranked flags (correlation, changepoint cluster, divergence, outlier regions).
- [ ] Deep-thinking LLM has interpreted Layer 2 output — mechanisms proposed, confounders identified, narrative patterns suggested.
- [ ] Human has reviewed findings summary and selected deep-dives to pursue.
- [ ] Layer 3 deep-dives have run for selected findings — notebooks with regression, lag, segmentation, or before/after analysis as appropriate.
- [ ] Custom hypotheses from `config.yaml` have been tested using narrative reframing patterns.

### Phase 4: Design the story

- [ ] Narrative LLM has proposed a story arc based on confirmed findings.
- [ ] Human has approved the narrative structure (what to lead with, sequence, takeaway).
- [ ] Chart types and annotations are decided for each finding.
- [ ] Story notebook outline exists.

### Phase 5: Execute & share

- [ ] Story notebook is complete with narrative prose + interactive Plotly charts.
- [ ] `run.py` has executed the notebook and exported to HTML.
- [ ] HTML report is in `projects/<name>/reports/`.
- [ ] Social-ready content (posts, summaries) has been generated and reviewed.
- [ ] Human has approved all outputs for publication.

## 5. Requirements

### Functional

- **FR-1:** Pipeline must support multiple concurrent projects without data or output cross-contamination.
- **FR-2:** Indicator schema must be open-ended — new categories and variables addable at any time via `config.yaml`.
- **FR-3:** Hypothesis definitions must support reusable narrative reframing patterns (masking, displacement, divergence, lag/lead, segmentation, threshold) with an extensible pattern library.
- **FR-4:** Analytical layers must be runnable independently (e.g., re-run Layer 2 without re-running Layer 1).
- **FR-5:** LLM assistance must be available at every phase via Cursor with appropriate model selection per phase.
- **FR-6:** All LLM outputs must be treated as proposals requiring human approval before inclusion in reports.
- **FR-7:** Single entrypoint (`run.py <project-name>`) must run the data-to-report pipeline for a given project.
- **FR-8:** Notebooks must be executable headlessly via nbconvert and exportable to standalone HTML.

### Non-functional

- **NFR-1:** Reproducibility — anyone with the repo and Python environment can re-run the full pipeline for any project.
- **NFR-2:** Isolation — a bug or bad data in one project must not affect any other project.
- **NFR-3:** Transparency — every data source, analytical decision, and LLM interaction is documented.

## 6. Assumptions

- Data sources are publicly available or obtainable without special access.
- Datasets fit in memory on a single machine (< ~10 GB per project for v1).
- User has access to Cursor with Claude, GPT-4o, o3, Gemini 2.5 Pro, and Perplexity models.
- Rigor level is journalistic / exploratory (not academic peer-review).

## 7. Change log

| Date | Change | Reason |
|------|--------|--------|
| 2026-03-02 | Initial BRD created | Pipeline documentation buildout |
