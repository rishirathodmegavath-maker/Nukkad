# Clarity — Round 2 Prototype Demo Video Script

**Team RishiXcenture — Accenture Innovation Challenge 2026, Round 2**
Teleprompter / read-aloud script with on-screen stage directions.
Target runtime: ~4 minutes. Bold = stress when speaking.

> I can't record or render video myself — this script is the substitute:
> read it aloud while screen-recording the app running locally
> (`npm run dev` on the frontend, `uvicorn app.main:app` on the backend).
> Every line below refers to something that is actually live in the app —
> nothing here is aspirational.

---

### [0:00–0:15] — HOOK

**[Screen: Dashboard, "Viewing as: Global Executive"]**

A dashboard can tell you Revenue in APAC fell 21%.

It can't tell you **why**, how sure to be about that, or **who's supposed to
act on it.**

**I'm Rishi, team RishiXcenture. This is Clarity — a KPI intelligence-to-action
engine, built for Round 2 of the Accenture Innovation Challenge.**

---

### [0:15–0:35] — WHAT'S NEW SINCE ROUND 1

**[Screen: Dashboard, scroll past the connectors panel and the 6 KPI cards]**

Round 1 proved the core loop: detect, explain, recommend.

Round 2 turns it into something an enterprise could actually govern: six KPI
scenarios across **five different source systems** and **four refresh
cadences**, a semantic contract per metric, role-based access control,
persona-tuned narratives, multi-dimensional root-cause search, and a real
feedback loop that changes future confidence — not just a bar that goes up.

---

### [0:35–1:00] — ACCESS CONTROL, LIVE

**[Screen: click the "Viewing as" role switcher in the top bar — switch from
Global Executive to APAC Regional Manager]**

Watch the dashboard change.

As Global Executive, I see all six KPIs.

Switch to **APAC Regional Manager** — and the list narrows to exactly the
one KPI this role owns.

**[Optionally: open dev tools or narrate] This isn't hidden in the UI — it's
enforced server-side. Requesting a KPI this role isn't entitled to returns
an HTTP 403, not a blank screen.**

Switch back to Global Executive.

---

### [1:00–1:45] — THE ANALYSIS PIPELINE, LIVE

**[Screen: click into "Revenue — APAC" (Critical)]**

Here's the raw signal — steady around $420K a day, then a hard drop, circled
by the anomaly detector.

**[Click "Explain this KPI" with persona = Executive]**

Watch the pipeline run: anomaly detection, root-cause attribution, evidence
retrieval, confidence scoring, action recommendation — **then**, only at the
end, the explanation is phrased.

**[Result appears]** Enterprise segment, down sharply, explains the bulk of
the change. Confidence in the high nineties. A materiality score blending
the statistical signal with a real dollar-impact estimate. And a decision
authority check — as Global Executive, I'm **authorized to act.**

**[Switch persona to Analyst, re-run]**

Same facts, different depth. The analyst view names the method, the
confidence breakdown, and — for this KPI — the **interaction effects**: which
combinations of traffic source and device compound each other, not just
single-dimension segments.

**[Switch persona to Ops Manager, re-run]**

And the ops view: **who to contact, today, no background noise.**

---

### [1:45–2:15] — HONESTY: ABSTENTION AND SPARSE HISTORY

**[Screen: navigate to "Churn Rate — Global SMB", run analysis]**

Here's the honest case. No single segment explains this move. Instead of
guessing, Clarity says so directly, drops confidence, and recommends a
**human deep-dive** instead of a false diagnosis.

**[Navigate to "Activation Rate — AI Copilot"]**

And here's a feature launched **12 days ago.** Not enough history for a
reliable trend — so confidence is capped, and instead of a bare low number,
Clarity benchmarks it against **comparable past feature launches** and says
plainly why that's the best available signal.

**That restraint is the point of this system, not a bug in it.**

---

### [2:15–2:45] — GOVERNANCE: THE CONTRACT

**[Screen: on any KPI detail page, click "View definition, lineage & access"]**

Every KPI carries a semantic contract: definition, calculation, data
lineage, source system, refresh cadence, an accountable **owner**, and
exactly which roles can see which fields.

**[Point at "Redacted for this role" if visible under a restricted role]**

Switch to a role without calculation access, and those fields are redacted
— **and the system tells you they were redacted**, rather than hiding that
fact.

---

### [2:45–3:10] — CONNECTORS AND FEEDBACK

**[Screen: back to Dashboard, point at the connectors panel]**

This isn't locked to synthetic data. A real SQL warehouse adapter and an
authenticated BI REST adapter are wired up and testable right now — they run
in seeded demo mode today because no production credentials are committed,
but the architecture is credential-ready, not a mockup.

**[Screen: back into an analysis result, scroll to feedback buttons, click 👍]**

And every analysis can be marked useful or not. That feedback is aggregated
— and once enough of it trends unfavorable for a KPI, the **next** analysis
run on that KPI has its confidence trimmed automatically, and says why.
**A real closed loop, not a button that goes nowhere.**

---

### [3:10–3:30] — AUDIT LOG

**[Screen: click "Audit Log" in the nav]**

Every run, logged: which persona, which role, the confidence, the cost, the
latency, and whether an LLM or the deterministic fallback wrote the
narrative. **Nothing here is a black box.**

---

### [3:30–4:00] — CLOSE

Statistics and rules decide what's real and what to do. Evidence and
confidence decide how much to trust it. An LLM only phrases it for a human.
Governed rules — not the model — decide the action.

That's Clarity: a days-long investigation, compressed to seconds, with an
owner, an audit trail, and an honest confidence score attached to every
answer.

**I'm Rishi, team RishiXcenture — this is Clarity, for Round 2.**

---

### TEAM RISHIXCENTURE
**Accenture Innovation Challenge 2026 — Round 2**
GitHub: https://github.com/rishirathodmegavath-maker/Nukkad
