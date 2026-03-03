# LLM Integration

All LLM work runs through **Cursor**. At each pipeline phase, the user opens a
Cursor session scoped to the current project and phase, selects the appropriate
model, and drives the work interactively. There is no separate API wrapper or
programmatic LLM call layer for v1.

---

## Execution model

1. **Cursor is the orchestration layer.** The user works in Cursor with the
   project directory open. Each phase has a recommended model and a defined
   scope of what the LLM should help with.
2. **Models are selected per phase** based on the task type (research, code,
   deep reasoning, narrative, writing). The user switches models in Cursor as
   they move through phases.
3. **LLM outputs are proposals.** Every LLM-generated artifact (data source
   list, cleaning code, interpretation, narrative draft, social post) is
   reviewed by the human before inclusion in the project.
4. **Interactions are logged.** Key LLM outputs are captured in the project's
   notebooks, decision log, or dedicated markdown files for reproducibility.

---

## LLM roles by phase

### Phase 1: Find (Data Discovery)

**Task:** Given the project's narrative hypothesis and indicator categories,
search for relevant datasets, evaluate source quality, and suggest indicator
categories the user hasn't considered.

**Recommended model:** Perplexity (purpose-built for research with citations)
or Gemini with search grounding.

**How to use in Cursor:**
1. Open a Cursor session with the project's `config.yaml` and `docs/data_catalog.md` template in context.
2. Select the research model.
3. Prompt: "Given this hypothesis and these indicator categories, find the best
   publicly available datasets. For each, provide: name, URL, format, time
   range, geographic granularity, update frequency, and license."
4. Review the output. Add approved sources to `config.yaml` and the project's
   data catalog.

**Output:** Populated `config.yaml` indicators and data sources sections;
updated data catalog.

### Phase 2: Study & Coalesce (Ingest, Clean, Merge)

**Task:** Analyze raw data schemas, flag quality issues, suggest join
strategies, generate cleaning code.

**Recommended model:** Claude (strong at code + data reasoning).

**How to use in Cursor:**
1. Open a Cursor session with sample raw data files and the project's
   `config.yaml` in context.
2. Select Claude.
3. Prompt: "Here are the raw data files for this project. Analyze the schemas,
   flag quality issues (nulls, type mismatches, outliers), suggest how to join
   these datasets, and generate the cleaning/merge scripts."
4. Review the generated code. Run it. Check the processed output.

**Output:** Ingest/clean/merge scripts (in `pipeline/` or project-specific);
processed Parquet files in `data/processed/`.

### Phase 3: Analyze — Layer 2 interpretation

**Task:** Interpret the statistical flags from Layer 1 and Layer 2. Propose
mechanisms behind correlations, identify confounders, suggest which narrative
reframing patterns to apply, and challenge the hypothesis.

**Recommended models (use 2+ and compare):**
- Claude with extended thinking
- OpenAI o3
- Gemini 2.5 Pro (thinking mode)

**Why multiple models:** Different reasoning models catch different things.
Comparing interpretations from 2–3 models is cheap insurance against blind
spots.

**How to use in Cursor:**
1. Open a Cursor session with the Layer 2 findings summary, the project's
   `config.yaml` (hypothesis + indicators), and `docs/analytical_framework.md`
   in context.
2. Select a deep-thinking model.
3. Prompt: "Here are the statistical findings from this study. For each flagged
   finding: (a) propose a mechanism that could explain it, (b) identify
   potential confounders, (c) suggest which narrative reframing pattern to apply
   (masking, displacement, divergence, lag, segmentation, threshold), and
   (d) actively challenge the narrative hypothesis — what alternative
   explanations should we consider?"
4. Repeat with a second model. Compare outputs.
5. Review and select which findings and interpretations to pursue in Layer 3.

**Output:** Annotated findings summary with mechanisms, confounders, and
recommended deep-dives.

### Phase 3: Analyze — Layer 3 interpretation

**Task:** Interpret deep-dive results (regression, lag, segmentation, etc.).
Assess whether findings are defensible, state caveats, and evaluate narrative
fit.

**Recommended models:** Same as Layer 2 (Claude thinking, o3, Gemini 2.5 Pro).

**How to use in Cursor:**
1. Open a Cursor session with the deep-dive notebook output and the project's
   hypothesis in context.
2. Prompt: "Here are the results of [regression / lag analysis / segmented
   comparison] for [finding]. Is this finding defensible at a journalistic
   level? What are the caveats? Does it support, refine, or contradict the
   hypothesis?"

**Output:** Interpreted deep-dive results with confidence assessment and
stated limitations.

### Phase 4: Design the Story

**Task:** Given confirmed findings, propose a narrative arc — what to lead
with, how to sequence the argument, chart types, headlines, and the "so what?"
takeaway.

**Recommended model:** Claude or GPT-4o (strong editorial / narrative
reasoning).

**How to use in Cursor:**
1. Open a Cursor session with the confirmed findings, interpreted deep-dives,
   and the project hypothesis in context.
2. Prompt: "Based on these confirmed findings, propose a narrative structure
   for the report. Include: headline, opening hook, sequence of sections
   (which finding first, how they build on each other), chart types and
   annotations for each section, and a closing takeaway. Target audience:
   social media / data forums."
3. Review and refine the structure before building the story notebook.

**Output:** Narrative outline (markdown) with section structure, chart specs,
and draft prose.

### Phase 5: Execute & Share

**Task:** Generate audience-specific content — social media posts (different
formats for X, LinkedIn, Reddit), executive summaries, report introductions,
chart annotations.

**Recommended model:** Claude or GPT-4o for narrative prose; a faster model
for generating social post variants.

**How to use in Cursor:**
1. Open a Cursor session with the final story notebook in context.
2. Prompt: "Generate social media posts for this report. Create versions for:
   (a) X/Twitter (280 chars, punchy), (b) LinkedIn (professional, 2-3
   paragraphs), (c) Reddit r/dataisbeautiful (conversational, methodology
   noted). Also generate a one-paragraph executive summary."

**Output:** Social-ready content in `reports/social/` or inline in the project
README.

---

## Guardrails

- **No auto-publish.** LLM-generated content is never published without human
  review and explicit approval.
- **No hallucinated data.** LLMs interpret data and propose narratives; they do
  not generate or modify data. All statistical results come from the pipeline's
  Python code.
- **Reproducibility.** Key LLM prompts and outputs are logged (in notebooks,
  decision log, or dedicated files) so the reasoning chain is traceable.
- **Challenge the hypothesis.** At Layer 2 and Layer 3, the LLM is explicitly
  asked to argue against the narrative and propose alternative explanations.
  This is a required step, not optional.

---

## Model selection quick reference

| Phase | Task type | Recommended model(s) |
|-------|-----------|---------------------|
| 1. Find | Research / web search | Perplexity, Gemini + Search |
| 2. Study & Coalesce | Code / data reasoning | Claude |
| 3. Analyze (Layer 2) | Deep interpretation | Claude thinking + o3 + Gemini 2.5 Pro (use 2+) |
| 3. Analyze (Layer 3) | Deep interpretation | Claude thinking + o3 + Gemini 2.5 Pro |
| 4. Design | Narrative / editorial | Claude, GPT-4o |
| 5. Execute & Share | Writing / content | Claude, GPT-4o, faster model for variants |
