import { useState } from 'react'
import type { AnalysisResult, KpiDetail } from '../lib/types'
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

export function AnalysisPanel({ kpi }: { kpi: KpiDetail }) {
  const [phase, setPhase] = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [activeStep, setActiveStep] = useState(0)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    setPhase('running')
    setActiveStep(0)
    setError(null)

    const resultPromise = api.analyzeKpi(kpi.id)
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

      {phase === 'idle' && (
        <div className="py-6 text-center">
          <p className="text-sm text-[var(--text-secondary)] mb-4 max-w-sm mx-auto">
            Run the full pipeline: anomaly detection → root-cause attribution → evidence retrieval → confidence
            scoring → natural-language explanation.
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
