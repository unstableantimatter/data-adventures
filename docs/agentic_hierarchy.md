# Agentic Hierarchy

Defines who does what in the pipeline — the human, the AI agents (via Cursor),
and the future cross-study analyst.

---

## Roles

### Human (Principal)

The human owns all decisions. Nothing is published, no phase advances, and no
data is trusted without explicit human approval.

**Responsibilities:**
- Own narrative and editorial decisions (what story to tell, what's defensible).
- Approve data source selections (what we trust and use).
- Approve phase transitions (e.g., "data is clean enough — move to Analyze").
- Review all LLM outputs before inclusion.
- Select which Layer 2 findings to pursue in Layer 3.
- Final review and approval of every published artifact.
- Manage the backlog and project queue.

### AI Agent (via Cursor)

The AI agent operates within a defined scope per phase and per project. It
proposes and executes; the human decides.

**Scope rules:**
- Scoped to one project at a time (no cross-project access).
- Scoped to one phase at a time (works within the current phase's boundaries).
- All outputs are proposals — never auto-published or auto-committed.

**Per-phase responsibilities and model assignments:**

| Phase | AI responsibility | Model |
|-------|------------------|-------|
| **1. Find** | Search for datasets, evaluate quality, suggest indicator categories | Perplexity / Gemini + Search |
| **2. Study & Coalesce** | Analyze schemas, flag quality issues, suggest joins, generate cleaning code | Claude |
| **3. Analyze — Layer 1** | Run automated descriptive pass (pipeline code; AI assists with debugging) | Claude |
| **3. Analyze — Layer 2** | Interpret flags, propose mechanisms, identify confounders, suggest patterns, challenge hypothesis | Claude thinking, o3, Gemini 2.5 Pro (use 2+) |
| **3. Analyze — Layer 3** | Interpret deep-dive results, assess defensibility, state caveats | Claude thinking, o3, Gemini 2.5 Pro |
| **4. Design** | Propose narrative arc, sequence findings, suggest charts, draft headlines | Claude, GPT-4o |
| **5. Execute & Share** | Build story notebook, generate social content, draft summaries | Claude, GPT-4o |

### Future: Cross-Study Analyst Agent

**Status:** Deferred until 3–4 studies are complete (see backlog item F-1).

**Design concept:**
- Has **read-only** access to all `projects/*/data/processed/` and
  `projects/*/reports/`.
- Periodically runs cross-project correlation analysis: looks for indicators
  that appear in multiple studies and flags unexpected relationships.
- Produces a "Cross-Study Findings" report with suggested new studies or
  deep-dives.
- Uses a deep-thinking model to interpret cross-project patterns.
- All outputs go to the human for review — the agent does not create new
  projects or modify existing ones.

**Implementation notes (for later):**
- Likely a dedicated Cursor session with all project data in context.
- Needs a cross-project indicator registry (union of all project indicators).
- Should be run after each new study is completed, not continuously.

---

## Phase transition protocol

The human approves every phase transition. The AI agent can recommend advancing
but cannot advance on its own.

**Before advancing from one phase to the next, verify:**

1. **Backlog updated** — project status in `backlog.md` reflects current phase.
2. **Acceptance criteria met** — check the BRD (`docs/BRD.md`) for the current
   phase's criteria.
3. **Data catalog current** — any new data sources are documented.
4. **Decision log updated** — any significant decisions made during the phase
   are recorded in `docs/decisions.md`.
5. **Human sign-off** — explicit approval to proceed.

---

## Guardrails summary

| Rule | Enforced by |
|------|------------|
| No cross-project data access | Directory isolation + scope rules |
| No auto-publishing | Human approval required at Phase 5 |
| LLM outputs are proposals | Human reviews before inclusion |
| Challenge the narrative | Required LLM prompt at Layer 2 and Layer 3 |
| Log decisions | Decision log updated at each phase transition |
| Multiple model comparison | Use 2+ deep-thinking models at Layer 2 |
