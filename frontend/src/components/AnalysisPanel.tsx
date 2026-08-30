import { useState } from 'react'
import type { AnalysisResult, FeedbackSummary, KpiDetail, Persona } from '../lib/types'
import { api } from '../lib/api'
import { BreakdownChart } from './BreakdownChart'

const PIPELINE_STEPS = [
  'Reading input signal',
  'Running anomaly detection',
  'Attributing root cause',
  'Retrieving corroborating evidence',
  'Scoring confidence',
  'Generating explanation',
]

const PERSONAS: { id: Persona; label: string }[] = [
  { id: 'executive', label: 'Executive' },
  { id: 'analyst', label: 'Analyst' },
  { id: 'ops_manager', label: 'Ops Manager' },
]

function ConfidenceMeter({ value, reasoning }: { value: number; reasoning: string }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.7 ? 'var(--good)' : value >= 0.45 ? 'var(--warning)' : 'var(--critical)'
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-xs font-medium text-[var(--text-secondary)]">AI confidence</span>
        <span className="text-sm font-semibold tabular" style={{ color }}>
          {pct}%
        </span>
      </div>
      <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--border)' }}>
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <p className="text-xs text-[var(--text-muted)] mt-1.5">{reasoning}</p>
    </div>
  )
}

function ActualVsExpected({ result, unit }: { result: AnalysisResult; unit: string }) {
  const deviating = Math.abs(result.expected_deviation_pct) >= 2
  return (
    <div className="rounded-lg border px-3 py-2" style={{ borderColor: 'var(--border)' }}>
      <div className="flex items-center justify-between text-xs">
        <span className="text-[var(--text-muted)]">Expected (trend-line forecast)</span>
        <span className="font-semibold tabular">
          {result.expected_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
          {unit}
        </span>
      </div>
      <p className="text-xs mt-1" style={{ color: deviating ? 'var(--warning)' : 'var(--text-muted)' }}>
        Actual is {result.expected_deviation_pct >= 0 ? '+' : ''}
        {result.expected_deviation_pct.toFixed(1)}% vs. what the pre-window trend would have predicted
        {deviating ? '' : ' — within normal forecast noise'}.
      </p>
    </div>
  )
}

function MaterialityMeter({ m }: { m: AnalysisResult['materiality'] }) {
  const pct = Math.round(m.score * 100)
  const color = m.score >= 0.7 ? 'var(--critical)' : m.score >= 0.4 ? 'var(--warning)' : 'var(--text-secondary)'
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-xs font-medium text-[var(--text-secondary)]">Materiality (signal + $ impact)</span>
        <span className="text-sm font-semibold tabular" style={{ color }}>
          {pct}%
        </span>
      </div>
      <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--border)' }}>
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <p className="text-xs text-[var(--text-muted)] mt-1.5">
        {m.estimated_impact} — {m.reasoning}
      </p>
    </div>
  )
}

function DecisionAuthorityNote({ d }: { d: AnalysisResult['decision_authority'] }) {
  return (
    <div
      className="rounded-lg border px-3 py-2 text-xs"
      style={{
        borderColor: d.can_authorize ? 'var(--good)' : 'var(--warning)',
        background: d.can_authorize ? 'var(--good-bg)' : 'var(--warning-bg)',
        color: 'var(--text-primary)',
      }}
    >
      <span className="font-semibold">{d.can_authorize ? 'Authorized to act' : 'Escalation required'}:</span> {d.note}
    </div>
  )
}

function ProcessingBreakdown({ steps }: { steps: AnalysisResult['processing_steps'] }) {
  return (
    <div>
      <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">
        LLM vs. deterministic breakdown
      </p>
      <ul className="space-y-1.5">
        {steps.map((s, i) => (
          <li key={i} className="text-xs flex items-start gap-2">
            <span
              className="shrink-0 rounded-full px-1.5 py-0.5 font-medium"
              style={{
                color: s.method === 'llm' ? 'var(--brand)' : 'var(--text-secondary)',
                background: s.method === 'llm' ? 'var(--brand-bg)' : 'var(--border)',
              }}
            >
              {s.method}
            </span>
            <span className="text-[var(--text-secondary)]">
              <span className="font-medium text-[var(--text-primary)]">{s.step}</span> — {s.detail}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function TelemetryFooter({ t }: { t: AnalysisResult['telemetry'] }) {
  return (
    <div className="text-[10px] text-[var(--text-muted)] flex flex-wrap gap-x-3 gap-y-1 pt-2 border-t" style={{ borderColor: 'var(--border)' }}>
      <span>latency {t.total_latency_ms.toFixed(1)}ms</span>
      <span>model calls {t.model_calls}</span>
      {t.model_calls > 0 && (
        <>
          <span>tokens {t.input_tokens}→{t.output_tokens}</span>
          <span>est. cost ${t.estimated_cost_usd.toFixed(6)}</span>
        </>
      )}
    </div>
  )
}

function FeedbackWidget({ kpiId, persona }: { kpiId: string; persona: Persona }) {
  const [sent, setSent] = useState<'useful' | 'not_useful' | null>(null)
  const [summary, setSummary] = useState<FeedbackSummary | null>(null)

  const send = async (useful: boolean) => {
    setSent(useful ? 'useful' : 'not_useful')
    try {
      await api.submitFeedback({ kpi_id: kpiId, persona, useful })
      const s = await api.getFeedbackSummary(kpiId)
      setSummary(s)
    } catch {
      /* feedback is best-effort telemetry, not critical path */
    }
  }

  if (sent) {
    return (
      <div className="text-xs text-[var(--text-muted)]">
        <p>Thanks — feedback recorded for this analysis.</p>
        {summary && summary.total_feedback > 0 && (
          <p className="mt-1">
            {summary.useful_count} of {summary.total_feedback} analyses on this KPI marked useful (
            {Math.round((summary.useful_rate ?? 0) * 100)}%). {summary.note}
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-[var(--text-muted)]">Was this explanation useful?</span>
      <button
        onClick={() => send(true)}
        className="rounded-md border px-2 py-1 hover:bg-[var(--border)]"
        style={{ borderColor: 'var(--border)' }}
      >
        👍 Yes
      </button>
      <button
        onClick={() => send(false)}
        className="rounded-md border px-2 py-1 hover:bg-[var(--border)]"
        style={{ borderColor: 'var(--border)' }}
      >
        👎 No
      </button>
    </div>
  )
}

export function AnalysisPanel({ kpi, role }: { kpi: KpiDetail; role: string }) {
  const [persona, setPersona] = useState<Persona>('executive')
  const [phase, setPhase] = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [activeStep, setActiveStep] = useState(0)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    setPhase('running')
    setActiveStep(0)
    setError(null)

    const resultPromise = api.analyzeKpi(kpi.id, persona, role)
    const stepTimer = new Promise<void>((resolve) => {
      let i = 0
      const interval = setInterval(() => {
        i += 1
        setActiveStep(i)
        if (i >= PIPELINE_STEPS.length - 1) {
          clearInterval(interval)
          resolve()
        }
      }, 260)
    })

    try {
      const [res] = await Promise.all([resultPromise, stepTimer])
      setResult(res)
      setPhase('done')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed')
      setPhase('error')
    }
  }

  return (
    <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
      <div className="flex items-center justify-between mb-1">
        <h3 className="font-semibold">AI Analysis</h3>
        {result && (
          <span
            className="text-xs rounded-full px-2 py-0.5 font-medium"
            style={{
              color: result.narrative_source === 'llm' ? 'var(--brand)' : 'var(--text-secondary)',
              background: result.narrative_source === 'llm' ? 'var(--brand-bg)' : 'var(--border)',
            }}
            title={result.narrative_source === 'llm' ? 'Narrative phrased by an LLM from pre-computed facts' : 'Offline deterministic template mode (no LLM key configured)'}
          >
            {result.narrative_source === 'llm' ? 'LLM-enhanced' : 'Template mode'}
          </span>
        )}
      </div>

      {phase !== 'running' && (
        <div className="flex items-center gap-1.5 my-3">
          {PERSONAS.map((p) => (
            <button
              key={p.id}
              onClick={() => setPersona(p.id)}
              className="text-xs rounded-full px-2.5 py-1 font-medium transition-colors"
              style={{
                background: persona === p.id ? 'var(--brand)' : 'var(--border)',
                color: persona === p.id ? 'white' : 'var(--text-secondary)',
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      )}

      {phase === 'idle' && (
        <div className="py-6 text-center">
          <p className="text-sm text-[var(--text-secondary)] mb-4 max-w-sm mx-auto">
            Run the full pipeline: anomaly detection → root-cause attribution → evidence retrieval → confidence
            scoring → {persona.replace('_', ' ')}-tuned explanation.
          </p>
          <button
            onClick={run}
            className="rounded-lg px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
            style={{ background: 'var(--brand)' }}
          >
            Explain this KPI
          </button>
        </div>
      )}

      {phase === 'running' && (
        <ul className="py-4 space-y-2.5">
          {PIPELINE_STEPS.map((step, i) => (
            <li key={step} className="flex items-center gap-2.5 text-sm">
              <span
                className="w-4 h-4 rounded-full flex items-center justify-center shrink-0 text-[10px]"
                style={{
                  background: i < activeStep ? 'var(--good)' : i === activeStep ? 'var(--brand)' : 'var(--border)',
                  color: i <= activeStep ? 'white' : 'transparent',
                }}
              >
                {i < activeStep ? '✓' : ''}
              </span>
              <span
                className={i === activeStep ? 'font-medium' : ''}
                style={{ color: i <= activeStep ? 'var(--text-primary)' : 'var(--text-muted)' }}
              >
                {step}
                {i === activeStep ? '…' : ''}
              </span>
            </li>
          ))}
        </ul>
      )}

      {phase === 'error' && (
        <div className="py-4 text-sm" style={{ color: 'var(--critical)' }}>
          {error}
        </div>
      )}

      {phase === 'done' && result && (
        <div className="space-y-5 mt-2">
          {result.is_ambiguous && (
            <div className="rounded-lg border px-3 py-2 text-xs" style={{ borderColor: 'var(--warning)', background: 'var(--warning-bg)', color: 'var(--text-primary)' }}>
              No single factor dominates this change. Treat this as a lead for human investigation, not a
              confirmed diagnosis.
            </div>
          )}

          <p className="text-sm leading-relaxed">{result.narrative}</p>

          <ActualVsExpected result={result} unit={kpi.unit} />

          <ConfidenceMeter value={result.confidence} reasoning={result.confidence_reasoning} />

          <MaterialityMeter m={result.materiality} />

          <DecisionAuthorityNote d={result.decision_authority} />

          {result.cohort_benchmark && (
            <div className="rounded-lg border px-3 py-2 text-xs" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
              <span className="font-semibold text-[var(--text-primary)]">Cohort benchmark: </span>
              {result.cohort_benchmark}
            </div>
          )}

          {result.known_drivers.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">
                Known / simulated drivers
              </p>
              <ul className="space-y-1 text-xs text-[var(--text-secondary)]">
                {result.known_drivers.map((d, i) => (
                  <li key={i}>• {d}</li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">
              Contributing factors ({kpi.dimension_label})
            </p>
            <BreakdownChart data={result.contributing_factors} />
          </div>

          {result.interaction_effects.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">
                Interaction effects (multi-dimensional)
              </p>
              <ul className="space-y-1.5">
                {result.interaction_effects.map((effect, i) => (
                  <li key={i} className="text-xs rounded-lg border px-3 py-2" style={{ borderColor: 'var(--border)' }}>
                    <span className="font-medium">{effect.segments.join(' x ')}</span>
                    <span className="text-[var(--text-secondary)]"> — {effect.contribution_pct.toFixed(0)}% contribution, {effect.pct_change.toFixed(1)}% movement, n={effect.sample_size.toLocaleString()}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">Evidence</p>
            <ul className="space-y-1.5">
              {result.evidence.map((e, i) => (
                <li key={i} className="text-xs rounded-lg border px-3 py-2" style={{ borderColor: 'var(--border)' }}>
                  <span className="font-medium">{e.source}</span>
                  <span className="text-[var(--text-secondary)]"> — "{e.text}"</span>
                  {e.document_id && (
                    <span className="block mt-1 text-[10px] text-[var(--text-muted)]">
                      doc {e.document_id} · score {(e.retrieval_score ?? 0).toFixed(3)} · {e.freshness} · {e.lineage}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">Recommended actions</p>
            <ul className="space-y-1.5">
              {result.recommended_actions.map((a, i) => (
                <li key={i} className="text-xs rounded-lg border px-3 py-2" style={{ borderColor: 'var(--border)' }}>
                  <span className="font-medium">{i + 1}. {a.action}</span>
                  <span className="block mt-1 text-[var(--text-secondary)]">Driver: {a.driver} · Lever: {a.lever} · Owner: {a.owner} · Confidence: {Math.round(a.confidence * 100)}%</span>
                  <span className="block mt-1 text-[var(--text-muted)]">Monitor: {a.monitoring_plan}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-lg border px-3 py-2 text-xs" style={{ borderColor: result.feedback_signal.recalibration_flag ? 'var(--warning)' : 'var(--border)' }}>
            <span className="font-semibold">Feedback learning: </span>{result.feedback_signal.note}
          </div>

          <ProcessingBreakdown steps={result.processing_steps} />

          <FeedbackWidget kpiId={kpi.id} persona={persona} />

          <TelemetryFooter t={result.telemetry} />

          <button
            onClick={run}
            className="text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] underline underline-offset-2"
          >
            Re-run analysis
          </button>
        </div>
      )}
    </div>
  )
}
