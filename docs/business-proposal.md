# Clarity — Detailed Business Proposal

**Accenture Innovation Challenge 2026 — Round 2**
**Problem Track 3: BusinessIntelligence.ai**
**Team RishiXcenture**

---

## Executive Summary

Every business runs on dashboards, and every dashboard eventually shows the
same kind of moment: a number moves. Revenue drops in a region, conversion
dips a point, churn ticks up. The dashboard is very good at showing *that*
it happened and almost useless at explaining *why*, *how sure we should be*,
and *what to do about it*. Today that translation is manual — an analyst
cross-references time series, segment breakdowns, tickets, and CRM notes,
and writes up a summary hours or days later, by which point the decision has
often already been made without the answer.

**Clarity** is a KPI intelligence-to-action engine that compresses that
investigation into one click. It detects materially significant KPI
movements, attributes them to the dimensional segments and interaction
effects most responsible, retrieves corroborating evidence from a governed
document corpus, scores its own confidence — including explicit abstention
when the data doesn't support a diagnosis — and produces a persona-specific,
audit-ready explanation with recommended actions, an accountable owner, and
a monitoring plan. An LLM is used strictly to phrase already-computed facts;
it never calculates a number or decides an action.

This document covers the problem, the solution design, who it's for, the
business case, a phased roadmap, and the risks we've identified and mitigated
— honestly, including what is not yet built.

---

## 1. Problem Framing

### 1.1 The core problem

A KPI storytelling engine has to answer three questions that a static
dashboard cannot:

1. **What actually changed, and does it matter?** Not every wiggle in a
   time series is worth an executive's attention — materiality is a
   function of both statistical significance and financial impact, and a
   dashboard has no concept of either.
2. **Why did it change, and how confident should we be in that answer?**
   Root-cause attribution across multiple business dimensions, corroborated
   with qualitative evidence, is exactly the kind of judgment call that
   static BI tooling cannot make — and it is dangerous to fake.
3. **What should we do about it, who owns that decision, and how do we know
   it worked?** A recommendation without an accountable owner and a
   monitoring plan is advice nobody is on the hook for.

### 1.2 Real-world complexity this design accounts for

Per the challenge brief, a production version of this system has to survive
conditions a demo can gloss over. We designed against these explicitly:

- **Heterogeneous sources, different grains and cadences.** Revenue,
  marketing, and operational data rarely live in the same system, refresh
  on the same clock, or agree on what a "region" is called. Clarity models
  this directly — every KPI carries a declared `source_system` and
  `refresh_cadence`, and confidence scoring includes a staleness penalty
  derived from how fresh the underlying source actually is.
- **Ambiguous, multi-causal movement.** Real KPI moves are rarely one clean
  story. Clarity's Conversion Rate — EMEA scenario is deliberately built
  with two overlapping causes (a checkout-latency regression *and* a
  broad-based channel decline) plus ranked two-dimensional interaction
  effects (traffic source × device), so the system has to reason about
  compounding causes, not just pick a single winner.
- **Sparse history.** A newly launched feature has no reliable trend
  baseline. Clarity's Activation Rate — AI Copilot scenario handles this by
  capping confidence honestly and falling back to a comparable-cohort
  benchmark instead of pretending 90 days of history exist.
- **Contradictory or insufficient evidence.** The Churn Rate — Global SMB
  scenario has low data completeness and no dominant segment; Clarity
  explicitly abstains — it lowers confidence and recommends a human
  deep-dive rather than manufacturing a confident-sounding guess.
- **Role-based personalization and access control.** Different consumers
  need different depth and are entitled to different data. A regional
  manager should not see another region's KPIs; an analyst gets full
  calculation/lineage detail, a business role does not. This is enforced
  server-side (HTTP 403, field-level redaction), never by hiding elements
  in the UI.
- **Cost, latency and auditability at scale.** Every analysis run records
  real latency, real token usage and estimated cost (read from the LLM
  provider's own usage response, not estimated), and is persisted to an
  audit log — because "how much is this costing us and can we explain any
  decision after the fact" are operational questions, not afterthoughts.

---

## 2. Solution Design

### 2.1 Pipeline

```
Business KPI data (multi-source, multi-cadence)
   -> Governed KPI semantic contract (definition, calculation, lineage, access, owner)
   -> Materiality detection (statistical significance x $ business impact)
   -> Root-cause attribution (dominant-segment ranking + 2-D interaction effects)
   -> Evidence retrieval (TF-IDF vector search over a documented evidence corpus)
   -> Confidence / abstention scoring (explainable, staleness- and history-aware)
   -> LLM narrative phrasing (facts-only prompt; persona-tuned; deterministic fallback)
   -> Governed recommended actions (driver -> lever -> action -> owner -> monitoring plan)
   -> Decision-rights check (can this role authorize the action, or must they escalate?)
   -> Feedback capture -> live confidence recalibration signal
   -> Persistent audit log of every run
```

### 2.2 Hybrid AI — deliberately not one model doing everything

| Task | Method | Why |
|---|---|---|
| Anomaly / trend detection | Rolling z-score + medium-term trend comparison (`numpy`) | Deterministic, auditable, no training data needed |
| Root-cause attribution | Rule-based contribution-share ranking + ranked interaction effects | A dominant-driver decision should be reproducible, not probabilistic |
| Materiality | Weighted formula: statistical significance + governed $-per-unit business impact | A statistically loud move can be financially trivial, and vice versa — one signal is not enough |
| Evidence retrieval | TF-IDF cosine retrieval over a versioned document corpus | Every citation carries a document ID, similarity score, freshness and lineage — not a black-box lookup |
| Confidence / abstention | Weighted formula: signal strength, data completeness, attribution clarity, evidence count, source freshness, history sufficiency, feedback trend | Every score ships with the plain-English reasoning behind it |
| Recommended actions | Fixed playbook keyed by status/ambiguity, structured as driver→lever→action→owner→monitoring plan | Action selection is exactly the kind of decision that should stay deterministic and auditable, not left to an LLM |
| Decision rights | Role-vs-KPI-owner check | A recommendation is not authorization; the system says explicitly who can act and who must escalate |
| Narrative generation | LLM (Anthropic Claude), persona-tuned, if configured — else a deterministic template | The LLM only phrases facts computed upstream; it never invents a number. No key configured, or the call fails? Falls back automatically — the system never goes down because of an external dependency |

### 2.3 Governance built in, not bolted on

- **Semantic contract per KPI** — definition, calculation, lineage, source
  system, refresh cadence, owner, materiality thresholds and access
  restrictions are all queryable (`GET /api/kpis/{id}/contract`), so every
  consumer agrees on what a number means.
- **Row/domain and field-level access control**, enforced server-side. A
  role not entitled to a KPI gets a 403, not a hidden UI element; a role
  entitled to view a KPI but not its calculation/lineage/raw evidence gets
  those fields redacted, with the redaction itself reported back
  (`redacted_fields`), not silently applied.
- **Configurable, credential-ready data connectors.** `/api/connectors`
  exposes a real SQL warehouse adapter and an authenticated BI REST
  adapter with live connection probes, alongside the seeded demo source —
  architecture that generalizes beyond synthetic data without a rebuild,
  activated by setting server-side credentials.
- **Feedback-driven recalibration.** Analysts mark an explanation useful or
  not; once a KPI accumulates enough unfavorable feedback, the *next* live
  analysis run has its confidence trimmed and says so explicitly — a real,
  if simple, closed loop rather than feedback captured and ignored.

---

## 3. Target Users

| Persona | What they need | What Clarity gives them |
|---|---|---|
| **Executive** | A fast, low-jargon answer: what happened, how much it matters, what to do | 2-3 sentence narrative, materiality score, the single most important action, no statistical vocabulary |
| **Analyst** | Enough detail to audit the conclusion themselves | Full method disclosure, confidence breakdown, interaction effects, evidence with retrieval score/freshness/lineage, unredacted calculation and lineage |
| **Ops / Regional Manager** | To know exactly who to contact and what to do, today | Direct, urgency-first phrasing naming the segment/team, plus a decision-rights check confirming whether they can act or must escalate |

Access is entitlement-scoped per role (global executive, regional manager
per region, product lead, analyst), so the same engine serves all three
without a rebuild per audience.

---

## 4. Business Case & Impact

### 4.1 Assumptions (stated explicitly, as the brief invites)

The BusinessIntelligence.ai track does not specify a reference deployment
scale, so we state our own: a mid-sized enterprise with roughly 50-150
actively monitored KPIs across 5-10 business units, generating on the order
of 200-500 materially significant movements per week that currently warrant
investigation. Each such investigation, done manually today, plausibly
consumes 2-6 analyst-hours (cross-referencing dashboards, running ad hoc
queries, searching tickets/CRM, writing up a summary).

### 4.2 Where the value comes from

- **Speed.** First-pass root-cause investigation drops from hours-to-days
  to seconds. At the assumed volume, that is roughly 400-3,000 analyst-hours
  per week of manual investigation work compressed into an on-demand,
  always-available first pass — not eliminating analyst judgment, but
  moving it from "manual data archaeology" to "review and confirm."
  Illustrative annualized reclaimed capacity at the low end of that range
  (~400 hrs/week) is over 20,000 analyst-hours per year.
- **Coverage.** Every monitored KPI gets an automated first pass, not just
  the ones an already-stretched analyst has time for — smaller-but-real
  anomalies stop going uninvestigated by default.
- **Trust and auditability.** Every analysis is logged with its confidence,
  its reasoning, its cost, and whether an LLM or the deterministic fallback
  produced it — turning AI-assisted decisions into something a compliance
  or audit function can actually review after the fact.
- **Honesty at scale.** Explicit abstention when evidence doesn't support a
  diagnosis is a risk-reduction feature, not a limitation — it is the
  difference between a system a business will trust after the first time it
  is wrong, and one it will not.
- **Enterprise fit.** The hybrid architecture (statistics decide what's
  real, rules decide what to do, the LLM only phrases) is exactly the kind
  of governed, explainable AI pattern that lets an enterprise put this in
  front of regulators and auditors, not just end users.

### 4.3 Cost discipline

The system is fully functional with zero external API keys (deterministic
template fallback), and when an LLM is used, real per-request token counts
and cost are captured from the provider's own usage response — so the
economics of scaling narrative generation are measured, not guessed at,
from day one.

---

## 5. Phased Roadmap

**Phase 0 — Delivered in this Round 2 prototype**
Multi-source/multi-cadence KPI model with governed semantic contracts;
materiality (statistical + $ impact); root-cause attribution with
two-dimensional interaction effects; TF-IDF evidence retrieval over a
versioned corpus; explainable confidence with staleness- and
history-awareness; persona-specific narratives; row/domain/field-level
access control; credential-ready warehouse and BI connectors; a live
feedback-to-confidence recalibration loop; full runtime telemetry; a
persistent audit log.

**Phase 1 — Pilot readiness (next ~90 days)**
Seasonality-aware anomaly detection (STL decomposition) to remove the
current naive-seasonality limitation; connect one real warehouse and one
real BI tool via the existing connector interface against a design-partner's
actual data; exhaustive three-plus-dimensional interaction search with
cardinality controls; expand the evidence corpus with real document
ingestion instead of curated samples.

**Phase 2 — Production hardening (6-12 months)**
OAuth-managed connector credentials and scheduled ingestion (replacing
manually-set environment variables); enterprise-scale embedding index with
document-level ACL propagation (today's TF-IDF index is a right-sized proof
of the retrieval mechanism, not the production-scale index); offline
evaluation and periodic model recalibration beyond today's live
feedback-trims-confidence signal; proper authentication in front of the
role parameter used in this prototype.

**Phase 3 — Scale-out**
Proactive Slack/email alerting when a KPI crosses into `watch` or `critical`;
multi-tenant deployment across additional business units; a governed
knowledge-graph layer over KPI/driver relationships to replace today's
per-KPI dimension configuration.

---

## 6. Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| **LLM hallucination or fabricated numbers** | The LLM receives only pre-computed facts in its prompt and is explicitly instructed never to invent a number; every number in the narrative traces back to a deterministic upstream calculation. A deterministic template fallback exists for when no LLM is configured or a call fails. |
| **Over-flagging (alert fatigue) or under-flagging (missed real issues)** | Materiality blends statistical significance with $-denominated business impact so noise doesn't reach the same bar as revenue-relevant moves; the threshold set is documented in each KPI's semantic contract and is centrally tunable. |
| **False confidence on ambiguous or sparse data** | Explicit abstention: when no segment dominates, or history is too short, or feedback trends unfavorable, confidence is deliberately capped and the reasoning is stated — the system is designed to say "I'm not sure" out loud. |
| **Data heterogeneity across sources** | Every KPI declares its source system, refresh cadence and calculation lineage in a governed semantic contract, so "whose definition of this number are we using" has one answer. |
| **Unauthorized data access / non-compliant sharing** | Row/domain-level entitlement is enforced server-side (403s, not client-side hiding); sensitive fields (calculation, lineage, raw evidence text) are redacted per role, with the redaction itself surfaced rather than silently applied. |
| **Cost and latency at scale** | Real per-request token/cost/latency telemetry from day one; deterministic fallback removes hard dependency on a live API; caching and batching are the explicit next optimization once real usage data exists. |
| **Recommendations issued without real authority to act on them** | Every recommended action is checked against the viewing role's decision rights — if the role does not own the KPI's domain, the system says explicitly that the action must be escalated, and to whom. |
| **Low adoption from a fatigued, skeptical user base** | Persona-tuned output (executive/analyst/ops manager) keeps each audience reading only what they need; the audit log and visible confidence reasoning are the trust-building mechanism that gets a system used instead of worked around. |

---

## 7. Why This Approach

The single most important design decision in Clarity is the separation of
concerns: **statistics and rules calculate the truth; evidence retrieval and
confidence scoring determine how much to trust it; an LLM only phrases it for
a human; governed business rules — not the LLM — decide what happens next.**
That separation is what makes every number in Clarity's output traceable,
auditable, and safe to put in front of an executive or a regulator — and it
is what the BusinessIntelligence.ai brief is explicitly asking teams to
demonstrate: "when do you use deterministic logic, SQL, business rules,
statistics... retrieval or LLMs — and why."

## 8. Links

- **GitHub repository:** https://github.com/rishirathodmegavath-maker/Nukkad
- **README (Round 2 requirements mapping in full):** see `README.md` §14 in
  the repository above
