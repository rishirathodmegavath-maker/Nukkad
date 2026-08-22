# Clarity — 3-Minute Demo Video Script

Format: screen recording of the running app (http://localhost:5173) with
voiceover. Timestamps are targets, not hard cuts — pace to what feels
natural when you rehearse it once.

---

## 0:00–0:20 — Hook

**Screen:** Dashboard page, hero section visible at top, KPI cards below.

**Narration:**
> "This dashboard says revenue in APAC just fell 21%. Here's the question
> every business leader asks next — *why* — and here's how long it usually
> takes an analyst to answer it: hours, sometimes days. We built something
> that answers it in three seconds. This is Clarity."

**Action:** Cursor hovers briefly over the "Revenue — APAC" card (status:
Critical, red badge) without clicking yet.

---

## 0:20–0:45 — Problem

**Screen:** Stay on dashboard; slowly scroll to show the hero copy ("The
problem / What Clarity does / Why AI is necessary").

**Narration:**
> "A dashboard can show you a number moved. It can't tell you why, what's
> driving it, or what to do next — that translation still falls to an
> analyst, manually cross-referencing charts, segment breakdowns, and
> support tickets. Meaningful anomalies get investigated. Everything else
> waits. That's the gap Clarity closes."

**Action:** No clicks — let the hero text be readable for ~5 seconds.

---

## 0:45–1:10 — Solution

**Screen:** Stay on dashboard, gesture (cursor) across the 5 KPI cards.

**Narration:**
> "Clarity watches every KPI, runs statistical anomaly detection to
> separate real signal from noise, and the moment something's worth
> explaining, it's one click away. Five metrics, five different stories —
> a critical anomaly, a slow-burn risk trend, a metric that already
> recovered, and one the system is honest enough to call ambiguous. Let's
> open the critical one."

**Action:** Click the "Revenue — APAC" card.

---

## 1:10–2:20 — LIVE PRODUCT DEMO (centerpiece)

**Screen:** KPI Detail page for Revenue — APAC loads: big number, trend
chart with a circled anomaly point, AI Analysis panel on the right showing
the "Explain this KPI" button.

**Narration:**
> "Here's the raw signal — revenue held steady around $420K a day, then
> dropped hard about ten days ago. The system already flagged it — that's
> the circled point, caught by a rolling anomaly detector, not a hardcoded
> alert. Now watch what happens when I ask it to explain."

**Action:** Click **"Explain this KPI."** Let the pipeline animation play
fully (≈1.5 seconds): *Reading input signal → Running anomaly detection →
Attributing root cause → Retrieving corroborating evidence → Scoring
confidence → Generating explanation.*

**Narration (during animation):**
> "It's not calling an LLM and hoping for the best — it's running a real
> pipeline: statistics decide what's real, rules attribute the cause,
> and only at the very end does it write the explanation in plain
> English."

**Screen:** Results render — narrative paragraph, confidence meter (98%,
green), contributing-factors bar chart (Enterprise channel dominant),
evidence card (CRM note about the TitanCorp account), recommended actions.

**Narration:**
> "There's the answer: Enterprise channel, down 79%, explains 150% of the
> total change — other channels partly offset it. It's backed by a real
> piece of evidence: a CRM note about a canceled enterprise renewal. 98%
> confidence, and it tells you exactly why it's confident. And it doesn't
> just diagnose — it recommends: escalate to the account owner within 24
> hours."

**Action:** Scroll down briefly to show the "Recommended actions" list,
then click the browser back button or the "← Back to dashboard" link.

**Screen:** Click into "Churn Rate — Global SMB" (the ambiguous scenario),
click "Explain this KPI" again (can speed up / skip animation in the edit).

**Narration:**
> "And here's the honest case. Churn ticked up slightly — but no single
> segment explains it. Instead of guessing, Clarity says so directly,
> drops its confidence to 21%, and recommends a human deep-dive instead of
> a false diagnosis. That restraint is the point."

---

## 2:20–2:45 — AI + Differentiation

**Screen:** Quick cut to the Audit Log page.

**Narration:**
> "Every one of these analyses is logged — what was asked, what was
> concluded, how confident the system was, whether the explanation came
> from an LLM or our offline fallback template. Nothing here is a black
> box. That's deliberate: this isn't one model doing everything — it's
> statistics and rules making the decisions, and an LLM used only to phrase
> them, with a deterministic fallback so the system is never dependent on
> an external API to function."

**Action:** Point at the audit table rows and the "Source" column badges.

---

## 2:45–3:00 — Impact + Closing

**Screen:** Cut back to the dashboard, all 5 KPI cards visible.

**Narration:**
> "A days-long investigation, down to seconds — for every metric, not just
> the ones that get attention, with an audit trail and an honest confidence
> score attached to every answer. This is Clarity: AI reinvention made
> real, for the analyst work that never had enough hours in the day."

**Action:** Hold on the dashboard for the final second. End card with the
team name / logo (per submission template).
