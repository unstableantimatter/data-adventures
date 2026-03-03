# Decision Log

Record of significant decisions made during pipeline design and project work.
Each entry has a date, the decision, and the rationale.

---

## Pipeline decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | **Pipeline-first architecture** — the repo is a reusable pipeline, not a single study. Each study is a project instance under `projects/`. | Enables running multiple studies without cross-contamination; the pipeline is the product. |
| 2026-03-02 | **Project isolation** — each project has its own `data/`, `notebooks/`, `reports/`, and `config.yaml`. No cross-project data access. | Prevents accidental cross-pollination of data or outputs between studies. |
| 2026-03-02 | **Python** as the primary language. | Standard for data work, Jupyter, Plotly, and the analytical libraries we need (scipy, statsmodels, ruptures, scikit-learn). |
| 2026-03-02 | **venv + requirements.txt** for environment management. | Simplest reproducible setup. Conda considered but overkill for pure Python. Can revisit if we need non-Python binary deps. |
| 2026-03-02 | **Plotly** for interactive charts (Altair as optional addition later). | Interactive, HTML-embeddable, good for storytelling and social sharing. |
| 2026-03-02 | **Jupyter notebooks** as the report artifact (not Quarto, not a custom app). | Notebooks are the deliverable — viewable in browser, runnable in Colab, exportable to HTML. No extra tooling needed. |
| 2026-03-02 | **nbconvert** for headless notebook execution and HTML export. | Built-in to Jupyter. Papermill only if we need parameterized runs later. |
| 2026-03-02 | **Single `run.py` entrypoint** for pipeline orchestration. | One command per project. Simpler than Makefile for our use case. |
| 2026-03-02 | **Journalistic / exploratory rigor level** (not academic). | Goal is compelling, defensible storytelling — not peer-reviewed causal inference. Can raise rigor level for specific studies if needed. |
| 2026-03-02 | **Semi-automated analysis** — Layer 1 and Layer 2 run automatically; Layer 3 is human-directed. | Balances automation with editorial control. The human decides what's worth investigating. |
| 2026-03-02 | **Flexible indicator schema** — open-ended categories, addable mid-study. | Studies need to explore non-obvious variable relationships (e.g., military recruitment masking unemployment). Fixed schemas would constrain this. |
| 2026-03-02 | **Custom hypothesis definitions** using narrative reframing patterns. | Standard correlations aren't enough. Need to test specific mechanisms (masking, displacement, divergence, etc.) that make compelling stories. |
| 2026-03-02 | **LLM integration via Cursor** — no custom API wrapper for v1. | The user drives each phase in Cursor using available models. Avoids building and maintaining a separate LLM orchestration layer. |
| 2026-03-02 | **Model selection per phase** — research models for Find, code models for coalesce, deep-thinking models for Analyze, narrative models for Design/Execute. | Different tasks need different model strengths. Using the cheapest adequate model per stage. |
| 2026-03-02 | **Multiple deep-thinking models at Layer 2** — use 2+ and compare interpretations. | Different reasoning models catch different things. Cheap insurance against blind spots in analytical interpretation. |
| 2026-03-02 | **Cross-Study Analyst Agent deferred** until 3–4 studies complete. | Not enough data to cross-analyze yet. Will revisit after the project queue has depth. |
