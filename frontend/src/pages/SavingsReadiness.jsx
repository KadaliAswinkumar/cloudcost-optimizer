import { useMemo, useState } from 'react'
import { CheckCircle2, Gauge, Lightbulb, Target } from 'lucide-react'

const QUESTIONS = [
  {
    id: 'billing_data',
    label: 'Billing data coverage',
    options: [
      { label: 'No cloud billing ingestion yet', score: 5 },
      { label: 'Single source connected (example: AWS only)', score: 15 },
      { label: 'Multi-source connected with fresh data', score: 25 },
    ],
  },
  {
    id: 'ownership',
    label: 'FinOps ownership',
    options: [
      { label: 'No owner assigned', score: 5 },
      { label: 'Part-time owner', score: 15 },
      { label: 'Dedicated owner with weekly cadence', score: 25 },
    ],
  },
  {
    id: 'execution',
    label: 'Optimization execution velocity',
    options: [
      { label: 'Recommendations not actioned', score: 5 },
      { label: 'Some actions implemented monthly', score: 15 },
      { label: 'Weekly implementation and verification', score: 25 },
    ],
  },
  {
    id: 'governance',
    label: 'Governance and controls',
    options: [
      { label: 'No guardrails', score: 5 },
      { label: 'Manual budget checks', score: 15 },
      { label: 'Policies, alerts, and anomaly response loop', score: 25 },
    ],
  },
]

function band(score) {
  if (score >= 80) return { level: 'Elite', color: 'text-emerald-300', advice: 'Scale automation and enterprise workflows.' }
  if (score >= 60) return { level: 'Strong', color: 'text-blue-300', advice: 'Push implementation velocity and verification depth.' }
  if (score >= 40) return { level: 'Developing', color: 'text-amber-300', advice: 'Improve onboarding and action ownership first.' }
  return { level: 'Early', color: 'text-rose-300', advice: 'Start with billing ingestion and weekly operating rhythm.' }
}

export default function SavingsReadiness() {
  const [answers, setAnswers] = useState({})

  const totalScore = useMemo(() => {
    return QUESTIONS.reduce((sum, q) => sum + (answers[q.id] ?? 0), 0)
  }, [answers])

  const readiness = band(totalScore)
  const completed = Object.keys(answers).length
  const coveragePct = Math.round((completed / QUESTIONS.length) * 100)

  const nextActions = useMemo(() => {
    const items = []
    if ((answers.billing_data ?? 0) < 25) {
      items.push('Connect all billing sources (CSV/FOCUS, CUR, Azure export, GCP billing) and enforce freshness checks.')
    }
    if ((answers.ownership ?? 0) < 25) {
      items.push('Assign a single FinOps owner and set a weekly savings review with engineering + finance.')
    }
    if ((answers.execution ?? 0) < 25) {
      items.push('Track recommendations through accepted -> in_progress -> implemented -> verified with target SLAs.')
    }
    if ((answers.governance ?? 0) < 25) {
      items.push('Enable anomaly response workflow and budget/risk guardrails across business-critical accounts.')
    }
    if (!items.length) {
      items.push('You are ready for advanced automation: rollout policies and auto-remediation with approval gates.')
    }
    return items
  }, [answers])

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <div className="flex items-center gap-2 text-primary-300 text-sm font-medium uppercase tracking-wide">
          <Gauge className="w-4 h-4" />
          Savings Readiness
        </div>
        <h1 className="text-3xl font-bold text-white mt-2">FinOps Readiness Score</h1>
        <p className="text-slate-400 mt-2">
          Fast founder-level diagnostic to estimate how quickly your org can convert cloud insights into verified savings.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <p className="text-xs text-slate-500">Current score</p>
          <p className={`text-3xl font-bold mt-1 ${readiness.color}`}>{totalScore}/100</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <p className="text-xs text-slate-500">Readiness band</p>
          <p className={`text-2xl font-semibold mt-1 ${readiness.color}`}>{readiness.level}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <p className="text-xs text-slate-500">Questionnaire completion</p>
          <p className="text-2xl font-semibold mt-1 text-white">{coveragePct}%</p>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-6">
        {QUESTIONS.map((q) => (
          <div key={q.id} className="space-y-2">
            <p className="text-sm font-medium text-white">{q.label}</p>
            <div className="grid gap-2">
              {q.options.map((opt) => (
                <button
                  key={opt.label}
                  type="button"
                  onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: opt.score }))}
                  className={`text-left px-3 py-2 rounded-lg border transition-colors ${
                    answers[q.id] === opt.score
                      ? 'border-primary-500/50 bg-primary-500/10 text-primary-200'
                      : 'border-slate-700 bg-slate-950/40 text-slate-300 hover:border-slate-500'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <div className="flex items-center gap-2 text-emerald-300 mb-3">
          <Target className="w-4 h-4" />
          <p className="font-medium">Recommended next move</p>
        </div>
        <p className="text-slate-300">{readiness.advice}</p>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <div className="flex items-center gap-2 text-sky-300 mb-3">
          <Lightbulb className="w-4 h-4" />
          <p className="font-medium">90-day execution plan</p>
        </div>
        <div className="space-y-2">
          {nextActions.map((item) => (
            <div key={item} className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5" />
              <p className="text-slate-300">{item}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
