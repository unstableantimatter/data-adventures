# Documentation Health Check — Checklist

Run this checklist periodically (after every phase transition, or at minimum
after every completed study) to catch drift between docs and reality.

**How to run:** Open a Cursor session with the full repo in context. Work
through each section below. The AI agent reads the referenced files and
flags inconsistencies. Fix issues inline before moving on.

---

## 1. Structure checks

These verify that the physical repo matches what the docs say exists.

- [ ] **Directory layout matches `docs/infrastructure.md`.**
  Compare the actual directory tree against the layout documented in
  `docs/infrastructure.md`. Flag any directories that exist but aren't
  documented, or that are documented but don't exist.

- [ ] **Every project in `backlog.md` has a directory.**
  Each entry in the Project Queue table should have a matching directory under
  `projects/`. Flag any mismatches.

- [ ] **Every project directory has required files.**
  Each `projects/<name>/` should contain: `config.yaml`, `README.md`,
  `data/raw/`, `data/processed/`, `notebooks/`, `reports/`. Flag missing items.

- [ ] **`docs/` contains all expected documents.**
  Cross-reference the documentation table in `README.md` against the actual
  files in `docs/`. Flag any missing or extra files.

---

## 2. Cross-reference checks

These verify that different docs agree with each other.

- [ ] **Tech stack in `docs/infrastructure.md` matches `requirements.txt`.**
  Every library listed in the infrastructure stack table should appear in
  `requirements.txt`. Flag any that are documented but not in requirements,
  or in requirements but not documented.

- [ ] **Backlog status is current.**
  Check each item in the pipeline backlog and project queue. Does the status
  reflect reality? (e.g., items marked "Planned" that are actually done, or
  "In progress" items that have stalled.)

- [ ] **Decision log is current.**
  Check `docs/decisions.md`. Has any significant decision been made since the
  last entry? Check recent git commits or conversation history for unlogged
  decisions.

- [ ] **BRD acceptance criteria match current pipeline capabilities.**
  Read the acceptance criteria in `docs/BRD.md`. Do they still reflect what
  the pipeline actually does? Flag criteria that have been met but not checked
  off, or criteria that no longer apply.

---

## 3. Per-project checks

Run these for each active project (status is not "Planned" or "Done").

- [ ] **`config.yaml` indicators match data catalog.**
  Every indicator in the project's `config.yaml` should have a corresponding
  row in the project's data catalog (in its `README.md` or a dedicated
  `data_catalog.md`). Flag indicators without catalog entries.

- [ ] **`config.yaml` data sources match `data/raw/` contents.**
  Every data source listed in `config.yaml` should have corresponding files
  in `data/raw/`. Flag sources without data, or data files without a source
  entry.

- [ ] **`config.yaml` hypotheses reference valid indicators.**
  Each hypothesis's `indicators` list should only reference indicators that
  exist in the indicators section. Flag orphaned references.

- [ ] **Project README status matches backlog.**
  The project's `README.md` phase status should match the backlog entry in
  `backlog.md`. Flag mismatches.

- [ ] **Project decision log is current.**
  Check the project's `README.md` decisions table. Any project-specific
  decisions made since the last entry?

---

## 4. Semantic checks (AI-assisted)

These require the AI agent to read and reason about content, not just
cross-reference fields.

- [ ] **`docs/analytical_framework.md` still describes what the pipeline does.**
  Read the framework doc and compare it to the actual pipeline code (if it
  exists yet). Are there analysis types documented that aren't implemented,
  or implemented features not documented?

- [ ] **`docs/llm_integration.md` model recommendations are still current.**
  Are the recommended models still available and still the best choice? Have
  new models been released that should be considered? Flag any that feel
  outdated.

- [ ] **`docs/agentic_hierarchy.md` roles match actual workflow.**
  Does the documented human/AI division of labor match how work is actually
  being done? Flag any roles that have shifted in practice.

- [ ] **No stale "Last updated" dates.**
  Check all files with "Last updated" footers. Flag any where the date is
  more than one phase transition ago.

---

## 5. After the review

- [ ] All flagged issues have been fixed or logged as backlog items.
- [ ] `docs/decisions.md` updated if any decisions were made during this review.
- [ ] "Last updated" dates refreshed on any modified files.
- [ ] This checklist's completion date recorded below.

---

## Review history

| Date | Reviewer | Issues found | Issues fixed |
|------|----------|-------------|-------------|
| — | — | — | — |
