# Data Adventures — Backlog

## What this is

A reusable, LLM-assisted data study pipeline. Each research project gets its own
isolated directory with data, notebooks, and reports. The pipeline automates the
path from raw data to published, shareable HTML with interactive charts.

---

## Per-project process (5 phases)

Every project follows these phases. LLM agents assist at each stage (see
`docs/llm_integration.md` and `docs/agentic_hierarchy.md`).

1. **Find** — Identify the best data sources (research LLM assists with discovery and quality evaluation).
2. **Study & coalesce** — Ingest, clean, and merge datasets into a coherent structure (code-reasoning LLM assists with schema analysis and cleaning).
3. **Analyze** — Run the three-layer analytical framework: automatic descriptive pass, flagging engine, and directed deep-dives (deep-thinking LLMs interpret findings and propose hypotheses).
4. **Design the story** — Decide narrative arc, visualizations, and sequencing (narrative LLM assists with story structure).
5. **Execute & share** — Produce notebooks, export to HTML, generate social-ready content (writing LLM assists with audience-specific outputs).

---

## Pipeline backlog

Items to build or improve in the pipeline itself.

| ID | Item | Status |
|----|------|--------|
| P-1 | Documentation suite (BRD, infrastructure, analytical framework, LLM integration, agentic hierarchy, decisions, data catalog) | Done |
| P-2 | Directory structure and project scaffolding | Done |
| P-3 | `run.py` — single entrypoint that runs data scripts, executes notebooks, exports HTML | Done |
| P-4 | Layer 1 — automatic descriptive pass (univariate profiles, trends, correlations, changepoints) | Done |
| P-5 | Layer 2 — flagging engine (rank findings by significance, divergence, outlier regions) | Done |
| P-6 | Layer 3 — directed deep-dive templates (regression, lag, segmentation, before/after, narrative threading) | Done |
| P-7 | Notebook export pipeline (nbconvert execution + HTML output to `reports/`) | Done |
| P-8 | Narrative reframing pattern library (masking, displacement, divergence, lag/lead, segmentation, threshold) | Done |
| P-9 | Docs health check — periodic review that validates all markdown docs against repo state, config, and each other. Script (`pipeline/docs_check.py`) + checklist (`docs/docs_review_checklist.md`) | Done (checklist); Planned (script) |

---

## Project queue

Research projects to run through the pipeline.

| ID | Project | Status | Directory |
|----|---------|--------|-----------|
| S-1 | Quality of Life in the USA vs. Immigration Trends | Phase 5 (Execute & share) | `projects/qol-immigration/` |

### S-1: Quality of Life in the USA vs. Immigration Trends

**Narrative to test:** How politicians have sold out the American people and
diluted their vote and the American knowledge base by systematically immigrating
susceptible populations and strategically placing them in districts and cities so
they can ensure the USA never moves away from the 2-party political system — and
how this has contributed to a substantial drop in quality of living in this
country for the 98% of Americans who are not millionaire+ rich.

*(The data work will either support, refine, or challenge this narrative.)*

---

## Future exploration

Items gated on prerequisites or deferred by design.

| ID | Item | Prerequisite | Notes |
|----|------|-------------|-------|
| F-1 | **Cross-Study Analyst Agent** — an agent with read access to all `projects/*/reports/` and `projects/*/data/processed/` that periodically cross-analyzes completed studies and flags correlations for further investigation | 3–4 completed studies | See `docs/agentic_hierarchy.md` for design notes |

---

*Last updated: 2026-03-04*
