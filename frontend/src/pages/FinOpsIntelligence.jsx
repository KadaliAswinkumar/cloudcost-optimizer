import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Sankey,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  BarChart3,
  Download,
  Globe2,
  Info,
  LayoutGrid,
  Loader2,
  PieChart as PieIcon,
  TrendingUp,
} from 'lucide-react'
import { api } from '../api/client'
import { formatApiError } from '../utils/apiError'

const COLORS = ['#22d3ee', '#a78bfa', '#fb923c', '#34d399', '#f472b6', '#60a5fa', '#fbbf24']

function formatUsd(n) {
  if (n == null || Number.isNaN(n)) return '—'
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(2)}K`
  return `$${Number(n).toFixed(2)}`
}

function RegionWordCloud({ items }) {
  if (!items?.length) return null
  const max = Math.max(...items.map((i) => i.weight))
  return (
    <div className="flex flex-wrap items-end justify-center gap-3 gap-y-4 min-h-[160px] p-4 rounded-xl bg-slate-900/60 border border-slate-800">
      {items.map((r) => {
        const size = 0.75 + (r.weight / max) * 1.25
        return (
          <span
            key={r.name}
            className="text-slate-100 font-semibold leading-tight text-center transition-transform hover:scale-105 cursor-default"
            style={{ fontSize: `${size}rem`, opacity: 0.85 + (r.weight / max) * 0.15 }}
            title={`${r.name}: ${formatUsd(r.cost_usd)}`}
          >
            {r.name}
          </span>
        )
      })}
    </div>
  )
}

export default function FinOpsIntelligence() {
  const [tab, setTab] = useState('billing')
  const [loading, setLoading] = useState(true)
  const [busyAction, setBusyAction] = useState('')
  const [error, setError] = useState(null)
  const [payload, setPayload] = useState(null)
  const [digest, setDigest] = useState(null)
  const [leaderboard, setLeaderboard] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [investorKpis, setInvestorKpis] = useState(null)
  const [whatIf, setWhatIf] = useState(null)
  const [selectedActionIds, setSelectedActionIds] = useState([])
  const [forecast, setForecast] = useState(null)
  const [commitmentPlan, setCommitmentPlan] = useState(null)
  const [narrative, setNarrative] = useState(null)
  const [copilotPlan, setCopilotPlan] = useState(null)
  const [copilotExecution, setCopilotExecution] = useState(null)
  const [policyEval, setPolicyEval] = useState(null)
  const [unitEconomics, setUnitEconomics] = useState(null)

  const [orgSlug, setOrgSlug] = useState('global')
  const [team, setTeam] = useState('All')
  const [provider, setProvider] = useState('')
  const [costType, setCostType] = useState('effective')
  const [groupBy, setGroupBy] = useState('provider')
  const [investorView, setInvestorView] = useState(false)

  const fetchDash = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [dashRes, digestRes, boardRes, anomalyRes, investorRes] = await Promise.all([
        api.getFinopsDashboard({
          team,
          provider: provider || undefined,
          cost_type: costType,
          organization_slug: orgSlug,
        }),
        api.getFinopsWeeklyDigest(orgSlug),
        api.getFinopsLeaderboard(),
        api.getFinopsAnomalies(orgSlug, false),
        api.getFinopsInvestorKpis(orgSlug),
      ])
      setPayload(dashRes.data)
      setDigest(digestRes.data)
      setLeaderboard(boardRes.data?.leaderboard || [])
      setAnomalies(anomalyRes.data?.anomalies || [])
      setInvestorKpis(investorRes.data?.kpis || null)
    } catch (e) {
      console.error(e)
      setError(formatApiError(e))
      setPayload(null)
    } finally {
      setLoading(false)
    }
  }, [team, provider, costType, orgSlug])

  useEffect(() => {
    fetchDash()
  }, [fetchDash])

  const runAction = async (kind, recommendationId) => {
    try {
      setBusyAction(recommendationId)
      const body = { organization_slug: orgSlug, actor: 'founder' }
      if (kind === 'accept') await api.acceptFinopsRecommendation(recommendationId, body)
      if (kind === 'in_progress') await api.markFinopsRecommendationInProgress(recommendationId, body)
      if (kind === 'implemented') await api.implementFinopsRecommendation(recommendationId, body)
      if (kind === 'verified') {
        await api.verifyFinopsRecommendation(recommendationId, {
          ...body,
          verification_notes: 'Verified by founder review',
        })
      }
      if (kind === 'rollback') {
        await api.rollbackFinopsRecommendation(recommendationId, {
          ...body,
          rollback_reason: 'Regression observed after rollout',
        })
      }
      if (kind === 'dismiss') await api.dismissFinopsRecommendation(recommendationId, body)
      await fetchDash()
    } catch (e) {
      setError(formatApiError(e))
    } finally {
      setBusyAction('')
    }
  }

  const runWhatIf = async () => {
    if (!selectedActionIds.length) return
    try {
      const { data } = await api.getFinopsWhatIf({
        organization_slug: orgSlug,
        recommendation_ids: selectedActionIds,
        adoption_probability: 0.7,
      })
      setWhatIf(data)
    } catch (e) {
      setError(formatApiError(e))
    }
  }

  const acknowledgeAnomaly = async (anomalyId) => {
    try {
      await api.acknowledgeFinopsAnomaly(anomalyId, { organization_slug: orgSlug, actor: 'founder' })
      await fetchDash()
    } catch (e) {
      setError(formatApiError(e))
    }
  }

  const downloadInvestorReport = async () => {
    try {
      const res = await api.exportFinopsInvestorReport(orgSlug)
      const blob = new Blob([res.data], { type: 'application/json' })
      const href = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = href
      a.download = `finops-investor-report-${orgSlug}.json`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(href)
    } catch (e) {
      setError(formatApiError(e))
    }
  }

  const runCopilotPlan = async () => {
    try {
      const recommendationIds = (payload?.top_actions || []).slice(0, 3).map((x) => x.recommendation_id)
      if (!recommendationIds.length) return
      const { data } = await api.createFinopsCopilotPlan({
        organization_slug: orgSlug,
        recommendation_ids: recommendationIds,
        risk_threshold: 0.6,
        approval_mode: 'auto_if_low_risk',
        change_window: 'business_hours',
        actor: 'founder',
      })
      setCopilotPlan(data)
    } catch (e) {
      setError(formatApiError(e))
    }
  }

  const runCopilotExecute = async () => {
    try {
      const recommendationIds = (payload?.top_actions || []).slice(0, 2).map((x) => x.recommendation_id)
      if (!recommendationIds.length) return
      const { data } = await api.runFinopsCopilotExecute({
        organization_slug: orgSlug,
        recommendation_ids: recommendationIds,
        approved: true,
        actor: 'founder',
        dry_run: false,
      })
      setCopilotExecution(data)
      await fetchDash()
    } catch (e) {
      setError(formatApiError(e))
    }
  }

  const runForecast = async () => {
    try {
      const { data } = await api.getFinopsForecast(orgSlug, 6)
      setForecast(data)
    } catch (e) {
      setError(formatApiError(e))
    }
  }

  const runCommitmentOptimizer = async () => {
    try {
      const { data } = await api.getFinopsCommitmentOptimizer(orgSlug)
      setCommitmentPlan(data)
    } catch (e) {
      setError(formatApiError(e))
    }
  }

  const runUnitEconomics = async () => {
    try {
      const { data } = await api.calculateFinopsUnitEconomics({
        organization_slug: orgSlug,
        monthly_revenue_usd: 240000,
        monthly_active_customers: 1500,
        monthly_transactions: 450000,
      })
      setUnitEconomics(data)
    } catch (e) {
      setError(formatApiError(e))
    }
  }

  const runPolicyEval = async () => {
    try {
      const { data } = await api.evaluateFinopsPolicy({
        organization_slug: orgSlug,
        policy_name: 'growth_guardrail_v1',
        max_unverified_actions: 6,
        min_confidence_score: 0.65,
        max_risk_score: 0.75,
        max_open_anomalies: 10,
        required_fresh_sources: 2,
      })
      setPolicyEval(data)
    } catch (e) {
      setError(formatApiError(e))
    }
  }

  const runExecutiveNarrative = async () => {
    try {
      const { data } = await api.getFinopsExecutiveNarrative(orgSlug)
      setNarrative(data)
    } catch (e) {
      setError(formatApiError(e))
    }
  }

  const focus = payload?.focus
  const executive = payload?.executive
  const mom = payload?.mom_trends
  const impact = payload?.impact
  const activation = payload?.activation
  const adoption = payload?.adoption
  const topActions = payload?.top_actions || []

  const serviceKeys = focus?.service_keys || []
  const providerKeys = useMemo(() => {
    const rows = focus?.cost_by_provider_monthly || []
    if (!rows.length) return []
    return Object.keys(rows[0]).filter((k) => !['month', 'month_label'].includes(k))
  }, [focus])
  const sankeyData = useMemo(() => {
    const s = focus?.sankey
    if (!s?.nodes?.length) return { nodes: [], links: [] }
    return { nodes: s.nodes.map((n) => ({ name: n.name })), links: s.links.map((l) => ({ ...l })) }
  }, [focus])
  const sankeyTopFlows = useMemo(() => {
    const links = sankeyData?.links || []
    const nodes = sankeyData?.nodes || []
    if (!links.length || !nodes.length) return []
    return [...links]
      .sort((a, b) => Number(b.value || 0) - Number(a.value || 0))
      .slice(0, 5)
      .map((l) => ({
        source: nodes[l.source]?.name || `node-${l.source}`,
        target: nodes[l.target]?.name || `node-${l.target}`,
        value: Number(l.value || 0),
      }))
  }, [sankeyData])
  const subBarKeys = focus?.sub_account_category_keys || []
  const dailyFamilies = useMemo(() => {
    const rows = executive?.daily_by_usage_family || []
    if (!rows.length) return []
    return Object.keys(rows[0]).filter((k) => k !== 'day' && k !== 'label')
  }, [executive])

  return (
    <div className="space-y-6 animate-fade-in max-w-[1600px] mx-auto">
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-primary-400 text-sm font-medium uppercase tracking-wide">
            <LayoutGrid className="w-4 h-4" />
            FinOps &amp; FOCUS
          </div>
          <h1 className="text-3xl font-bold text-white mt-1">Cost Intelligence Hub</h1>
          <p className="text-slate-400 mt-2 max-w-2xl">
            Build traction with measurable savings: detect waste, execute actions, and prove realized impact.
          </p>
        </div>
        <label className="inline-flex items-center gap-2 text-sm text-slate-300">
          <input type="checkbox" checked={investorView} onChange={(e) => setInvestorView(e.target.checked)} />
          Investor view
        </label>
      </div>

      {payload?.meta?.data_mode === 'demo' && (
        <div className="flex items-start gap-2 text-amber-200/90 text-sm bg-amber-500/10 border border-amber-500/25 rounded-lg px-3 py-2">
          <Info className="w-4 h-4 shrink-0 mt-0.5" />
          <span>Demo dataset + seeded actions. Connect live billing ingestion to convert to production values.</span>
        </div>
      )}

      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-2">
        {[
          { id: 'billing', label: 'Billing summary (FOCUS)' },
          { id: 'executive', label: 'Executive FinOps' },
          { id: 'mom', label: 'MoM trends' },
          { id: 'growth', label: 'Growth loops' },
          { id: 'next', label: 'Next-level' },
          { id: 'about', label: 'About' },
        ].map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t.id
                ? 'bg-primary-500/20 text-primary-300 border border-primary-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/80'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 p-4 rounded-xl bg-slate-900/40 border border-slate-800">
        <label className="flex flex-col gap-1 text-xs text-slate-500">
          Organization slug
          <input
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
            value={orgSlug}
            onChange={(e) => setOrgSlug(e.target.value || 'global')}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-slate-500">
          Team / shared view
          <select value={team} onChange={(e) => setTeam(e.target.value)} className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
            {(payload?.filters?.teams || ['All']).map((x) => <option key={x} value={x}>{x}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-slate-500">
          Provider
          <select value={provider} onChange={(e) => setProvider(e.target.value)} className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
            <option value="">All providers</option>
            {(payload?.filters?.providers || []).filter(Boolean).map((p) => <option key={p} value={p}>{p.toUpperCase()}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-slate-500">
          Cost basis
          <select value={costType} onChange={(e) => setCostType(e.target.value)} className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
            {(payload?.filters?.cost_types || ['effective', 'amortized', 'cash']).map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <div className="flex flex-col gap-1 text-xs text-slate-500">
          <span className="flex items-center gap-1"><Globe2 className="w-3 h-3" /> Refresh</span>
          <button type="button" onClick={() => fetchDash()} className="bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white">Reload data</button>
        </div>
      </div>

      {loading && <div className="flex items-center gap-2 text-slate-400 py-12 justify-center"><Loader2 className="w-6 h-6 animate-spin" />Loading dashboard…</div>}
      {error && <div className="rounded-lg border border-red-500/40 bg-red-500/10 text-red-200 px-4 py-3 text-sm">{typeof error === 'string' ? error : JSON.stringify(error)}</div>}

      {!loading && payload && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <p className="text-xs text-slate-500">Detected opportunity</p>
            <p className="text-2xl font-semibold text-white mt-1">{formatUsd(impact?.recommended_savings_usd)}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <p className="text-xs text-slate-500">Implemented savings</p>
            <p className="text-2xl font-semibold text-emerald-300 mt-1">{formatUsd(impact?.implemented_savings_usd)}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <p className="text-xs text-slate-500">Realized savings (30d)</p>
            <p className="text-2xl font-semibold text-emerald-400 mt-1">{formatUsd(impact?.realized_savings_30d_usd)}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <p className="text-xs text-slate-500">Activation (hours)</p>
            <p className="text-2xl font-semibold text-white mt-1">{activation?.time_to_first_saving_hours ?? '—'}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <p className="text-xs text-slate-500">Accept rate</p>
            <p className="text-2xl font-semibold text-white mt-1">{adoption?.recommendation_accept_rate?.toFixed?.(1) ?? adoption?.recommendation_accept_rate ?? 0}%</p>
          </div>
        </div>
      )}

      {!loading && investorKpis && investorView && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
            <p className="text-xs text-slate-500">Action events (30d)</p>
            <p className="text-lg text-white font-semibold">{investorKpis.action_events_30d}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
            <p className="text-xs text-slate-500">Accepted / Implemented</p>
            <p className="text-lg text-white font-semibold">
              {investorKpis.recommendations_accepted} / {investorKpis.recommendations_implemented}
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
            <p className="text-xs text-slate-500">Avg confidence</p>
            <p className="text-lg text-white font-semibold">{(Number(investorKpis.average_confidence_score || 0) * 100).toFixed(1)}%</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
            <p className="text-xs text-slate-500">Payback period</p>
            <p className="text-lg text-white font-semibold">{investorKpis.payback_period_months} mo</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3 col-span-2 md:col-span-4 flex justify-end">
            <button
              type="button"
              onClick={downloadInvestorReport}
              className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm border border-violet-500/40 bg-violet-500/10 text-violet-200 hover:bg-violet-500/20"
            >
              <Download className="w-4 h-4" />
              Export investor report
            </button>
          </div>
        </div>
      )}

      {!loading && payload && tab === 'billing' && (
        <div className="space-y-8">
          {!investorView && (
            <>
              <section>
                <h2 className="text-lg font-semibold text-white mb-2 flex items-center gap-2"><Globe2 className="w-5 h-5 text-primary-400" />Regions by effective cost (India-first showcase)</h2>
                <RegionWordCloud items={focus?.region_word_cloud} />
              </section>

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                  <h3 className="text-white font-medium mb-4 flex items-center gap-2"><BarChart3 className="w-5 h-5 text-cyan-400" />Effective cost by service (USD)</h3>
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={focus?.cost_by_service_monthly || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="month_label" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                        <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} tickFormatter={(v) => formatUsd(v)} />
                        <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} formatter={(v) => formatUsd(v)} />
                        <Legend />
                        {serviceKeys.map((k, i) => <Bar key={k} dataKey={k} stackId="svc" fill={COLORS[i % COLORS.length]} name={k.toUpperCase()} />)}
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>

                <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                  <h3 className="text-white font-medium mb-4">Effective cost by provider + trend</h3>
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={focus?.cost_by_provider_monthly || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="month_label" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" tickFormatter={(v) => formatUsd(v)} />
                        <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} formatter={(v) => formatUsd(v)} />
                        <Legend />
                        {providerKeys.map((k, i) => <Bar key={k} dataKey={k} fill={COLORS[i % COLORS.length]} />)}
                        {providerKeys[0] ? <Line type="monotone" dataKey={providerKeys[0]} stroke="#fbbf24" strokeWidth={2} dot={false} name="Trend (primary series)" /> : null}
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </section>
              </div>

              <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                  <h3 className="text-white font-medium">Group by (drill-down hooks)</h3>
                  <div className="flex flex-wrap gap-2">
                    {(focus?.group_by_options || []).map((g) => (
                      <button key={g} type="button" onClick={() => setGroupBy(g)} className={`text-xs px-3 py-1.5 rounded-full border ${groupBy === g ? 'border-primary-500/50 bg-primary-500/15 text-primary-200' : 'border-slate-700 text-slate-400 hover:border-slate-500'}`}>{g.replace(/_/g, ' ')}</button>
                    ))}
                  </div>
                </div>
                <div className="h-[340px] w-full overflow-x-auto rounded-lg bg-slate-950/50 border border-slate-800/60 p-2">
                  <ResponsiveContainer width="100%" height="100%" minWidth={700}>
                    <Sankey
                      data={sankeyData}
                      nodeWidth={14}
                      nodePadding={22}
                      margin={{ left: 28, right: 140, top: 24, bottom: 24 }}
                      node={{ stroke: '#38bdf8', fill: '#0ea5e9' }}
                      link={{ stroke: '#7dd3fc', strokeOpacity: 0.45 }}
                    >
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} formatter={(v) => formatUsd(v)} />
                    </Sankey>
                  </ResponsiveContainer>
                </div>
                {sankeyTopFlows.length ? (
                  <div className="mt-3 grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
                    {sankeyTopFlows.map((flow) => (
                      <div key={`${flow.source}-${flow.target}`} className="rounded-md border border-slate-800 bg-slate-950/60 px-2 py-1.5">
                        <p className="text-xs text-slate-300">{flow.source} → {flow.target}</p>
                        <p className="text-xs text-sky-300">{formatUsd(flow.value)}</p>
                      </div>
                    ))}
                  </div>
                ) : null}
              </section>

              <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                <h3 className="text-white font-medium mb-4">Effective cost by sub-account / scope</h3>
                <div className="h-[340px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart layout="vertical" data={focus?.sub_account_bars || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis type="number" stroke="#94a3b8" tickFormatter={(v) => formatUsd(v)} />
                      <YAxis type="category" dataKey="name" width={160} stroke="#94a3b8" tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} formatter={(v) => formatUsd(v)} />
                      <Legend />
                      {subBarKeys.map((k, i) => <Bar key={k} dataKey={k} stackId="sub" fill={COLORS[i % COLORS.length]} name={k} />)}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </section>
            </>
          )}

          <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="text-white font-medium mb-4">Top 10 actions this week</h3>
            <div className="space-y-3">
              {topActions.map((a) => (
                <div key={a.recommendation_id} className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                  <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-2">
                    <div>
                      <p className="text-sm text-white font-medium">{a.title}</p>
                      <p className="text-xs text-slate-400">
                        {a.cloud_provider?.toUpperCase()} · {a.effort_level} effort · confidence {(a.confidence_score * 100).toFixed(0)}% ({a.confidence_level})
                      </p>
                      <p className="text-xs text-slate-500">
                        status {a.status} · risk {(Number(a.risk_score || 0) * 100).toFixed(0)}% · blast {a.blast_radius} · bucket {a.decision_bucket}
                      </p>
                      <p className="text-xs text-emerald-300 mt-1">Estimated: {formatUsd(a.estimated_monthly_savings_usd)} / month</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button type="button" disabled={busyAction === a.recommendation_id} onClick={() => runAction('accept', a.recommendation_id)} className="px-3 py-1.5 rounded-md text-xs bg-sky-500/20 border border-sky-500/40 text-sky-200">Accept</button>
                      <button type="button" disabled={busyAction === a.recommendation_id} onClick={() => runAction('in_progress', a.recommendation_id)} className="px-3 py-1.5 rounded-md text-xs bg-indigo-500/20 border border-indigo-500/40 text-indigo-200">In progress</button>
                      <button type="button" disabled={busyAction === a.recommendation_id} onClick={() => runAction('implemented', a.recommendation_id)} className="px-3 py-1.5 rounded-md text-xs bg-emerald-500/20 border border-emerald-500/40 text-emerald-200">Implemented</button>
                      <button type="button" disabled={busyAction === a.recommendation_id} onClick={() => runAction('verified', a.recommendation_id)} className="px-3 py-1.5 rounded-md text-xs bg-emerald-500/20 border border-emerald-500/40 text-emerald-100">Verify</button>
                      <button type="button" disabled={busyAction === a.recommendation_id} onClick={() => runAction('rollback', a.recommendation_id)} className="px-3 py-1.5 rounded-md text-xs bg-amber-500/20 border border-amber-500/40 text-amber-200">Rollback</button>
                      <button type="button" disabled={busyAction === a.recommendation_id} onClick={() => runAction('dismiss', a.recommendation_id)} className="px-3 py-1.5 rounded-md text-xs bg-slate-500/20 border border-slate-500/40 text-slate-200">Dismiss</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {!loading && payload && tab === 'executive' && executive && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900/80 to-slate-950 p-6"><p className="text-sm text-slate-400">Spend YTD — amortized</p><p className="text-3xl font-bold text-white mt-2">{formatUsd(executive.spend_ytd_amortized_usd)}</p></div>
            <div className="rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900/80 to-slate-950 p-6"><p className="text-sm text-slate-400">Spend YTD — cash</p><p className="text-3xl font-bold text-white mt-2">{formatUsd(executive.spend_ytd_cash_usd)}</p></div>
            <div className="rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900/80 to-slate-950 p-6"><p className="text-sm text-slate-400">Monthly estimated (amortized)</p><p className="text-2xl font-bold text-emerald-400 mt-2">{formatUsd(executive.monthly_estimated?.current_amortized_usd)}</p></div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <h3 className="text-white font-medium mb-2 flex items-center gap-2"><PieIcon className="w-5 h-5 text-violet-400" />Cost by cloud vendor (quarter)</h3>
              <div className="h-[260px]"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={executive.vendor_pie} dataKey="percent" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>{executive.vendor_pie.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></div>
            </section>
            <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <h3 className="text-white font-medium mb-2">Spend by cost center</h3>
              <div className="h-[260px]"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={executive.cost_center_pie} dataKey="percent" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={100} label>{executive.cost_center_pie.map((_, i) => <Cell key={i} fill={COLORS[(i + 2) % COLORS.length]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></div>
            </section>
          </div>
          <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="text-white font-medium mb-4">Daily costs by usage family</h3>
            <div className="h-[330px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={executive.daily_by_usage_family || []}><CartesianGrid strokeDasharray="3 3" stroke="#334155" /><XAxis dataKey="label" stroke="#94a3b8" tick={{ fontSize: 10 }} interval={4} /><YAxis stroke="#94a3b8" tickFormatter={(v) => formatUsd(v)} /><Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} formatter={(v) => formatUsd(v)} /><Legend wrapperStyle={{ fontSize: 11 }} />{dailyFamilies.map((f, i) => <Bar key={f} dataKey={f} stackId="u" fill={COLORS[i % COLORS.length]} />)}</BarChart></ResponsiveContainer></div>
          </section>
        </div>
      )}

      {!loading && payload && tab === 'mom' && mom && (
        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2"><TrendingUp className="w-5 h-5 text-emerald-400" />Month-over-month trend — multi-cloud</h3>
          <div className="h-[380px]"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={mom.series || []}><CartesianGrid strokeDasharray="3 3" stroke="#334155" /><XAxis dataKey="label" stroke="#94a3b8" /><YAxis stroke="#94a3b8" tickFormatter={(v) => formatUsd(v)} /><Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} formatter={(v) => formatUsd(v)} /><Legend /><Bar dataKey="aws_usd" name="AWS" fill="#ff9900" /><Bar dataKey="azure_usd" name="Azure" fill="#0078d4" /><Bar dataKey="gcp_usd" name="GCP" fill="#34a853" /><Line type="monotone" dataKey="total_usd" stroke="#e2e8f0" strokeWidth={2} name="Total" /></ComposedChart></ResponsiveContainer></div>
        </section>
      )}

      {!loading && payload && tab === 'growth' && (
        <div className="space-y-6">
          <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="text-white font-medium mb-2">Weekly digest (auto narrative)</h3>
            <p className="text-sm text-slate-400">Actions in last 7 days: {(digest?.changes || []).length}</p>
            <div className="mt-3 grid sm:grid-cols-2 gap-3">
              {(digest?.next_best_actions || []).map((n) => (
                <label key={n.recommendation_id} className="flex items-start gap-2 rounded-lg border border-slate-800 p-3">
                  <input
                    type="checkbox"
                    checked={selectedActionIds.includes(n.recommendation_id)}
                    onChange={(e) => {
                      setSelectedActionIds((prev) => e.target.checked ? [...prev, n.recommendation_id] : prev.filter((x) => x !== n.recommendation_id))
                    }}
                  />
                  <span className="text-sm text-slate-200">{n.title}</span>
                </label>
              ))}
            </div>
            <div className="mt-3 flex gap-2">
              <button type="button" onClick={runWhatIf} className="px-3 py-2 rounded-md bg-primary-600 text-white text-sm">Run what-if planner</button>
              {whatIf ? <p className="text-sm text-emerald-300">Projected annual savings: {formatUsd(whatIf.projected_annual_savings_usd)}</p> : null}
            </div>
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="text-white font-medium mb-4">Savings leaderboard</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead><tr className="text-slate-500 border-b border-slate-800"><th className="py-2 text-left">Org</th><th className="py-2 text-right">Realized</th><th className="py-2 text-right">Est.</th><th className="py-2 text-right">Rate</th></tr></thead>
                <tbody>
                  {leaderboard.map((row) => (
                    <tr key={row.organization_slug} className="border-b border-slate-800/70 text-slate-200">
                      <td className="py-2">{row.organization_slug}</td>
                      <td className="py-2 text-right">{formatUsd(row.realized_monthly_savings_usd)}</td>
                      <td className="py-2 text-right">{formatUsd(row.estimated_monthly_savings_usd)}</td>
                      <td className="py-2 text-right">{row.realization_rate}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="text-white font-medium mb-4">Anomalies & regressions</h3>
            {anomalies.length === 0 ? (
              <p className="text-sm text-slate-500">No open anomalies.</p>
            ) : (
              <div className="space-y-2">
                {anomalies.map((a) => (
                  <div key={a.id} className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm text-white">{a.anomaly_type} · {a.metric_name}</p>
                      <p className="text-xs text-slate-400">
                        baseline {formatUsd(a.baseline_value)} → observed {formatUsd(a.observed_value)} ({a.deviation_pct}%)
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => acknowledgeAnomaly(a.id)}
                      className="px-3 py-1.5 rounded-md text-xs bg-slate-700 border border-slate-500 text-slate-100"
                    >
                      Acknowledge
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {!loading && payload && tab === 'next' && (
        <div className="space-y-6">
          <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="text-white font-medium mb-3">Autonomous Savings Copilot</h3>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={runCopilotPlan} className="px-3 py-2 rounded-md bg-sky-600 text-white text-sm">Generate copilot plan</button>
              <button type="button" onClick={runCopilotExecute} className="px-3 py-2 rounded-md bg-indigo-600 text-white text-sm">Execute approved actions</button>
            </div>
            {copilotPlan ? (
              <div className="mt-3 text-sm text-slate-300">
                <p>Planned actions: {copilotPlan.summary?.recommendation_count} · Estimated savings: {formatUsd(copilotPlan.summary?.estimated_monthly_savings_usd)}</p>
              </div>
            ) : null}
            {copilotExecution ? (
              <p className="mt-2 text-sm text-emerald-300">Copilot execution updates: {copilotExecution.updated_count}</p>
            ) : null}
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="text-white font-medium mb-3">Forecast + Commitment Optimizer</h3>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={runForecast} className="px-3 py-2 rounded-md bg-emerald-600 text-white text-sm">Run 6-month forecast</button>
              <button type="button" onClick={runCommitmentOptimizer} className="px-3 py-2 rounded-md bg-violet-600 text-white text-sm">Generate commitment plan</button>
            </div>
            {forecast ? (
              <p className="mt-3 text-sm text-slate-300">Latest projected month: {formatUsd(forecast.projection?.[forecast.projection.length - 1]?.projected_realized_savings_usd)}</p>
            ) : null}
            {commitmentPlan ? (
              <div className="mt-2 text-sm text-slate-300">
                <p>Coverage estimate: {commitmentPlan.coverage_estimate_pct}%</p>
                <p>Unlocked savings gap: {formatUsd(commitmentPlan.unlocked_savings_gap_usd)}</p>
              </div>
            ) : null}
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="text-white font-medium mb-3">Unit Economics + Policy-as-Code</h3>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={runUnitEconomics} className="px-3 py-2 rounded-md bg-amber-600 text-white text-sm">Calculate unit economics</button>
              <button type="button" onClick={runPolicyEval} className="px-3 py-2 rounded-md bg-rose-600 text-white text-sm">Evaluate FinOps policy</button>
            </div>
            {unitEconomics ? (
              <p className="mt-3 text-sm text-slate-300">
                Cost/customer: {formatUsd(unitEconomics.unit_metrics?.cloud_cost_per_customer_usd)} · Gross margin: {unitEconomics.unit_metrics?.gross_margin_pct}%
              </p>
            ) : null}
            {policyEval ? (
              <p className={`mt-2 text-sm ${policyEval.passed ? 'text-emerald-300' : 'text-amber-300'}`}>
                Policy status: {policyEval.passed ? 'passed' : 'violations found'} ({(policyEval.violations || []).length} issues)
              </p>
            ) : null}
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="text-white font-medium mb-3">Executive Narrative Generator</h3>
            <button type="button" onClick={runExecutiveNarrative} className="px-3 py-2 rounded-md bg-primary-600 text-white text-sm">Generate narrative</button>
            {narrative ? (
              <pre className="mt-3 whitespace-pre-wrap text-xs text-slate-300 bg-slate-950/60 rounded-lg p-3 border border-slate-800">
                {narrative.narrative_markdown}
              </pre>
            ) : null}
          </section>
        </div>
      )}

      {!loading && payload && tab === 'about' && (
        <div className="max-w-none rounded-xl border border-slate-800 bg-slate-900/40 p-6 text-slate-300">
          <h2 className="text-white text-xl font-semibold mb-4">FOCUS &amp; traction system</h2>
          <ul className="list-disc pl-5 space-y-3 text-sm leading-relaxed">
            <li>One command center tracks detected opportunity, implemented actions, and realized savings in one place.</li>
            <li>All onboarding paths are supported: CSV/FOCUS, AWS CUR, Azure export, GCP billing, API push.</li>
            <li>Growth loops include weekly digests, leaderboard comparison, and what-if forecasting.</li>
          </ul>
          <p className="text-xs text-slate-500 mt-6">Meta: {payload?.meta?.updated_at} — {payload?.meta?.notes}</p>
        </div>
      )}
    </div>
  )
}
