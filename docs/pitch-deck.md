# Clarity — 3-Slide Pitch Deck Content

Per the official Round 1 brief, the concept deck is capped at **3 slides**
(problem statement + concept/approach + why it matters). Use the official
`AIC_Talent-Brand_PPT-Template.pptx` — Arial font, standard alignment,
spell-checked, all team-detail fields filled in (mandatory). The team-details
slide from the template still applies before these 3 content slides; it is
not one of the 3.

---

## Slide 1 — The Problem

**Headline:** A KPI drop is easy to see. Explaining it takes days.

- Dashboards report *that* revenue dropped 8% — never *why*, or *what to do*
- Root-cause analysis today = an analyst manually cross-referencing charts,
  segment breakdowns, tickets, and CRM notes
- Typical turnaround: **hours to days** — by which point the decision already
  had to be made without the answer
- Smaller-but-real anomalies go uninvestigated simply because no analyst had
  the time
- Affects every function that watches a number move: revenue, growth,
  retention, ops — anyone accountable for "what happened and what do we do"

**Visual suggestion:** a dashboard tile showing "Revenue –8%" with a large
"?" — versus the same tile with a one-line AI explanation underneath.

---

## Slide 2 — Our AI Solution

**Headline:** Clarity — click "Explain this KPI," get a defensible answer in seconds.

**Pipeline:** Input signal → Anomaly detection → Root-cause attribution →
Evidence retrieval → Confidence scoring → Natural-language explanation →
Recommended action

**Key innovation — hybrid AI, not one model doing everything:**
- Statistics (rolling z-score + trend) decide *what's real*
- Rules rank *which segment* is responsible and *what to do about it*
- An LLM is used **only** to phrase already-computed facts into plain
  English — never to invent a number
- No LLM key configured? Falls back to a deterministic template
  automatically — zero downtime, zero cost to demo

**Responsible AI, built in, not bolted on:**
- Every confidence score ships with its reasoning, in plain English
- When no cause dominates, Clarity says so explicitly and lowers confidence
  instead of guessing
- Every analysis is written to a persistent, queryable audit log

**Visual suggestion:** the pipeline diagram above, plus a screenshot of the
AI Analysis panel (narrative + confidence meter + breakdown chart).

---

## Slide 3 — Impact

**Headline:** From a days-long investigation to a 3-second, audit-ready answer.

- **Speed:** first-pass root-cause investigation in seconds instead of days
- **Coverage:** every monitored KPI gets analyzed, not just the ones that
  get an analyst's attention
- **Trust:** confidence scores and audit logs make every AI-assisted
  decision explainable and reviewable after the fact
- **Honesty at scale:** ambiguous cases are flagged, not papered over —
  critical for avoiding false confidence in high-stakes business decisions
- **Scalability:** the architecture (stats → rules → LLM-for-phrasing) is
  metric-agnostic — plug in any KPI source (warehouse, BI tool API) without
  redesigning the pipeline
- **Enterprise fit:** exactly the kind of AI-augmented analyst workflow
  Accenture's own consulting practice depends on — turning it into a
  reusable product, not a one-off dashboard

**Visual suggestion:** a simple before/after: "Analyst investigation: 4-8
hours" vs. "Clarity: <10 seconds," plus the 5-scenario status spread from the
live dashboard (critical / watch / recovered / normal / ambiguous) to show
range, not a single lucky demo.
