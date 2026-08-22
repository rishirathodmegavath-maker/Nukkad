# 200-word submission content

## A) Problem Statement (~200 words)

Every business runs on dashboards, and every dashboard eventually shows the
same kind of moment: a number moves. Revenue drops 8% in a region, conversion
dips a point, churn ticks up. The dashboard is very good at showing *that* it
happened and almost useless at explaining *why*. Answering that question today
means an analyst manually cross-referencing time series, drilling into
regional and channel breakdowns, searching support tickets and CRM notes for
context, and finally writing up a summary for leadership — a process that
routinely takes hours to days, even when the underlying cause is already
sitting in the data.

That delay is expensive twice over: decisions wait on it, and by the time the
explanation arrives, the business context that produced the anomaly has often
moved on. It also means root-cause analysis only happens for the metrics that
get someone's attention — smaller but still meaningful shifts go
uninvestigated simply because no analyst had the hours.

The challenge, as Accenture frames it under BusinessIntelligence.ai, is to
design an AI system that explains in natural language what changed in a
business metric, identifies likely root causes using both structured and
unstructured data, and recommends next steps — separating meaningful signal
from ordinary noise, and being honest about when the answer is genuinely
ambiguous.

## B) Proposed Solution (~200 words)

Clarity is an AI KPI storytelling engine that compresses that entire
investigation into one click. It continuously runs statistical anomaly
detection (rolling z-score plus medium-term trend comparison) across
monitored KPIs to separate real signal from normal noise, then automatically
attributes any meaningful change to the dimensional segment most responsible
— region, channel, cohort, or traffic source — by ranking each segment's
share of the total movement.

It then pulls corroborating qualitative evidence (CRM notes, support tickets,
incident logs, product analytics) that a human would otherwise have to search
for manually, and scores its own confidence using a transparent formula: how
strong is the statistical signal, how complete is the underlying data, how
clearly does one segment dominate, and how much evidence corroborates it.

Only then does an LLM step in — strictly to phrase the already-computed facts
into a plain-English narrative and recommendation, never to invent a number.
If no LLM is configured, Clarity falls back to a deterministic template
automatically, so it never goes offline.

Crucially, when no single cause dominates, Clarity says so explicitly and
lowers its confidence rather than manufacturing a confident-sounding guess —
turning what took an analyst days into an auditable, honest answer in seconds.
