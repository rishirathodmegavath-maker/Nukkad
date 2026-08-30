import { useState } from 'react'
import type { AnalysisResult, KpiDetail, Persona } from '../lib/types'
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

  const send = async (useful: boolean) => {
    setSent(useful ? 'useful' : 'not_useful')
    try {
      await api.submitFeedback({ kpi_id: kpiId, persona, useful })
    } catch {
      /* feedback is best-effort telemetry, not critical path */
    }
  }

  if (sent) {
    return <p className="text-xs text-[var(--text-muted)]">Thanks — feedback recorded for this analysis.</p>
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

          <ConfidenceMeter value={result.confidence} reasoning={result.confidence_reasoning} />

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

          <div>
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">Evidence</p>
            <ul className="space-y-1.5">
              {result.evidence.map((e, i) => (
                <li key={i} className="text-xs rounded-lg border px-3 py-2" style={{ borderColor: 'var(--border)' }}>
                  <span className="font-medium">{e.source}</span>
                  <span className="text-[var(--text-secondary)]"> — "{e.text}"</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">Recommended actions</p>
            <ul className="space-y-1.5">
              {result.recommended_actions.map((a, i) => (
                <li key={i} className="text-sm flex items-start gap-2">
                  <span className="mt-0.5 text-[var(--brand)]">{i + 1}.</span>
                  {a}
                </li>
              ))}
            </ul>
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
