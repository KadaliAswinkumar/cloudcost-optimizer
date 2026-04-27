import { useCallback, useEffect, useMemo, useState } from 'react'
import { RadioTower, Play, RefreshCw, FileJson, AlertCircle, ChevronRight, X } from 'lucide-react'
import { api } from '../api/client'
import { formatApiError } from '../utils/apiError'

const LS_ORG_ID = 'cloudcost_intel_org_id'

const severityStyles = {
  critical: 'bg-red-500/15 text-red-300 border-red-500/30',
  high: 'bg-orange-500/15 text-orange-300 border-orange-500/30',
  medium: 'bg-amber-500/15 text-amber-200 border-amber-500/30',
  low: 'bg-slate-500/15 text-slate-300 border-slate-500/30',
  info: 'bg-blue-500/10 text-blue-200 border-blue-500/20',
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

export default function InfraIntelligence() {
  const [orgId, setOrgId] = useState(() => localStorage.getItem(LS_ORG_ID) || '')
  const [orgName, setOrgName] = useState('My Organization')
  const [orgSlug, setOrgSlug] = useState('')
  const [connectors, setConnectors] = useState([])
  const [connectorName, setConnectorName] = useState('Primary AWS')
  const [awsCredsJson, setAwsCredsJson] = useState(
    '{\n  "access_key_id": "",\n  "secret_access_key": "",\n  "session_token": null,\n  "region": "us-east-1"\n}'
  )
  const [selectedConnectorId, setSelectedConnectorId] = useState('')
  const [scans, setScans] = useState([])
  const [activeScan, setActiveScan] = useState(null)
  const [findings, setFindings] = useState([])
  const [selectedFinding, setSelectedFinding] = useState(null)
  const [reportExportUrl, setReportExportUrl] = useState('')
  const [pageError, setPageError] = useState('')
  const [busy, setBusy] = useState(false)

  const hasOrg = Boolean(orgId)

  const loadConnectors = useCallback(async () => {
    if (!orgId) return
    const { data } = await api.intelligence.listConnectors(orgId)
    setConnectors(data)
    setSelectedConnectorId((prev) => {
      if (prev && data.some((c) => c.id === prev)) return prev
      return data[0]?.id || ''
    })
  }, [orgId])

  const loadScans = useCallback(async () => {
    if (!orgId) return
    const { data } = await api.intelligence.listScans(orgId, { limit: 20 })
    setScans(data)
  }, [orgId])

  const verifyOrg = useCallback(async () => {
    const stored = localStorage.getItem(LS_ORG_ID)
    if (!stored) return
    try {
      await api.intelligence.getOrganization(stored)
      setOrgId(stored)
      setPageError('')
    } catch {
      localStorage.removeItem(LS_ORG_ID)
      setOrgId('')
      setPageError('Saved workspace was removed. Create a new organization below.')
    }
  }, [])

  useEffect(() => {
    verifyOrg()
  }, [verifyOrg])

  useEffect(() => {
    if (!orgId) return
    loadConnectors().catch((e) => setPageError(formatApiError(e)))
    loadScans().catch(() => {})
  }, [orgId, loadConnectors, loadScans])

  const pollScan = async (scanId) => {
    const max = 60
    for (let i = 0; i < max; i += 1) {
      const { data } = await api.intelligence.getScan(orgId, scanId)
      setActiveScan(data)
      if (data.status === 'completed' || data.status === 'failed') {
        await loadScans()
        if (data.status === 'completed') {
          const fr = await api.intelligence.listFindings(orgId, { scan_id: scanId })
          setFindings(fr.data)
        } else {
          setFindings([])
        }
        return data
      }
      await sleep(150)
    }
    throw new Error('Scan timed out while polling — try again or check API logs.')
  }

  const createOrg = async () => {
    setPageError('')
    setBusy(true)
    try {
      const slug =
        orgSlug.trim() ||
        `org-${typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID().slice(0, 8) : String(Date.now()).slice(-8)}`
      const { data } = await api.intelligence.createOrganization({
        name: orgName.trim() || 'Organization',
        slug: slug.toLowerCase().replace(/[^a-z0-9-]/g, '-'),
      })
      localStorage.setItem(LS_ORG_ID, data.id)
      setOrgId(data.id)
    } catch (e) {
      setPageError(formatApiError(e))
    } finally {
      setBusy(false)
    }
  }

  const addConnector = async () => {
    setPageError('')
    setBusy(true)
    try {
      let credentials = {}
      try {
        credentials = JSON.parse(awsCredsJson || '{}')
      } catch {
        throw new Error('Connector credentials must be valid JSON.')
      }
      await api.intelligence.createConnector(orgId, {
        provider: 'aws',
        display_name: connectorName.trim() || 'AWS',
        credentials,
      })
      await loadConnectors()
    } catch (e) {
      setPageError(formatApiError(e))
    } finally {
      setBusy(false)
    }
  }

  const runScan = async () => {
    if (!selectedConnectorId) {
      setPageError('Select or add a connector first.')
      return
    }
    setPageError('')
    setBusy(true)
    setActiveScan(null)
    setFindings([])
    try {
      const { data, status } = await api.intelligence.triggerScan(orgId, selectedConnectorId, {
        trigger: 'manual',
      })
      if (status !== 202 && status !== 200) {
        throw new Error(`Unexpected status ${status}`)
      }
      setActiveScan(data)
      await pollScan(data.id)
    } catch (e) {
      setPageError(formatApiError(e))
    } finally {
      setBusy(false)
    }
  }

  const generateReport = async () => {
    if (!activeScan?.id || activeScan.status !== 'completed') {
      setPageError('Complete a scan before generating a report.')
      return
    }
    setBusy(true)
    setPageError('')
    setReportExportUrl('')
    try {
      const title = `Infra report ${new Date().toISOString().slice(0, 19)}`
      const { data } = await api.intelligence.createReport(orgId, {
        title,
        scan_job_ids: [activeScan.id],
      })
      setReportExportUrl(api.intelligence.exportReportUrl(orgId, data.id))
    } catch (e) {
      setPageError(formatApiError(e))
    } finally {
      setBusy(false)
    }
  }

  const downloadReport = () => {
    if (!reportExportUrl) return
    window.open(reportExportUrl, '_blank', 'noopener,noreferrer')
  }

  const findingsSorted = useMemo(
    () =>
      [...findings].sort((a, b) => {
        const order = { critical: 0, high: 1, medium: 2, low: 3, info: 4 }
        return (order[a.severity] ?? 9) - (order[b.severity] ?? 9)
      }),
    [findings]
  )

  return (
    <div className="space-y-8 animate-fade-in max-w-6xl mx-auto">
      <div className="text-center py-8">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 mb-4">
          <RadioTower className="w-7 h-7 text-emerald-400" />
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">
          Infrastructure Intelligence
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
          Connect read-only AWS inventory, run scans in the background, review findings with
          evidence, and export JSON reports. GCP/Azure use the demo graph until collectors ship.
        </p>
      </div>

      {pageError && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-100"
        >
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{pageError}</span>
        </div>
      )}

      {!hasOrg ? (
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white">Create workspace</h2>
          <p className="text-sm text-slate-400">
            One organization per browser for now (stored locally). Production will use server
            accounts and SSO.
          </p>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Display name</label>
              <input
                className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-white text-sm"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Slug (optional, lowercase)
              </label>
              <input
                className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-white text-sm"
                placeholder="my-company"
                value={orgSlug}
                onChange={(e) => setOrgSlug(e.target.value)}
              />
            </div>
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={createOrg}
            className="btn-primary inline-flex items-center gap-2 disabled:opacity-50"
          >
            {busy ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4" />}
            Create organization
          </button>
        </div>
      ) : (
        <>
          <div className="glass-card p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-white">AWS connector</h2>
              <span className="text-xs text-slate-500 font-mono">org {orgId.slice(0, 8)}…</span>
            </div>
            <p className="text-sm text-slate-400">
              Leave keys empty to run a <strong className="text-slate-300">demo stub</strong> scan.
              For live inventory, use IAM keys scoped per <code className="text-xs text-slate-300">docs/AWS_INFRA_INTELLIGENCE_IAM.md</code> in the repo.
            </p>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Connector name</label>
                <input
                  className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-white text-sm"
                  value={connectorName}
                  onChange={(e) => setConnectorName(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Existing connector</label>
                <select
                  className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-white text-sm"
                  value={selectedConnectorId}
                  onChange={(e) => setSelectedConnectorId(e.target.value)}
                >
                  <option value="">— select —</option>
                  {connectors.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.display_name} ({c.provider})
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Credentials JSON (never shown again after save)
              </label>
              <textarea
                className="w-full min-h-[140px] rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-white text-xs font-mono"
                value={awsCredsJson}
                onChange={(e) => setAwsCredsJson(e.target.value)}
              />
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                disabled={busy}
                onClick={addConnector}
                className="px-4 py-2 rounded-xl bg-slate-800 border border-slate-600 text-white text-sm font-medium hover:bg-slate-700 disabled:opacity-50"
              >
                Save connector
              </button>
              <button
                type="button"
                disabled={busy || !selectedConnectorId}
                onClick={runScan}
                className="btn-primary inline-flex items-center gap-2 disabled:opacity-50"
              >
                {busy ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Run scan (async)
              </button>
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <div className="glass-card p-6">
              <h3 className="text-md font-semibold text-white mb-3">Recent scans</h3>
              {scans.length === 0 ? (
                <p className="text-sm text-slate-500">No scans yet.</p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {scans.map((s) => (
                    <li
                      key={s.id}
                      className="flex justify-between gap-2 rounded-lg bg-slate-900/60 border border-slate-800 px-3 py-2"
                    >
                      <span className="font-mono text-xs text-slate-400 truncate">{s.id}</span>
                      <span
                        className={`shrink-0 text-xs font-medium ${
                          s.status === 'completed'
                            ? 'text-emerald-400'
                            : s.status === 'failed'
                              ? 'text-red-400'
                              : 'text-amber-300'
                        }`}
                      >
                        {s.status}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              {activeScan && (
                <div className="mt-4 p-3 rounded-lg bg-slate-900/80 border border-slate-700 text-xs text-slate-300 space-y-1">
                  <div>
                    <span className="text-slate-500">Active:</span> {activeScan.status}
                  </div>
                  {activeScan.error_message && (
                    <div className="text-red-300 break-words">{activeScan.error_message}</div>
                  )}
                </div>
              )}
            </div>

            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-md font-semibold text-white">Findings</h3>
                <span className="text-xs text-slate-500">{findingsSorted.length} items</span>
              </div>
              {findingsSorted.length === 0 ? (
                <p className="text-sm text-slate-500">
                  {activeScan?.status === 'failed'
                    ? 'Scan failed — fix credentials or IAM and retry.'
                    : 'Run a completed scan to populate findings.'}
                </p>
              ) : (
                <div className="overflow-x-auto max-h-80 overflow-y-auto rounded-lg border border-slate-800">
                  <table className="w-full text-left text-sm">
                    <thead className="sticky top-0 bg-slate-900/95 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="p-2">Severity</th>
                        <th className="p-2">Category</th>
                        <th className="p-2">Title</th>
                        <th className="p-2 text-right">Est. $/mo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {findingsSorted.map((f) => (
                        <tr
                          key={f.id}
                          className="border-b border-slate-800/60 hover:bg-slate-800/40 cursor-pointer"
                          onClick={() => setSelectedFinding(f)}
                        >
                          <td className="p-2">
                            <span
                              className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${
                                severityStyles[f.severity] || severityStyles.info
                              }`}
                            >
                              {f.severity}
                            </span>
                          </td>
                          <td className="p-2 text-slate-300">{f.category}</td>
                          <td className="p-2 text-white">{f.title}</td>
                          <td className="p-2 text-right text-slate-300 font-mono text-xs">
                            {f.estimated_monthly_savings != null
                              ? String(f.estimated_monthly_savings)
                              : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={busy || activeScan?.status !== 'completed'}
                  onClick={generateReport}
                  className="px-4 py-2 rounded-xl bg-slate-800 border border-slate-600 text-white text-sm inline-flex items-center gap-2 hover:bg-slate-700 disabled:opacity-50"
                >
                  <FileJson className="w-4 h-4" />
                  Generate JSON report
                </button>
                {reportExportUrl && (
                  <button
                    type="button"
                    onClick={downloadReport}
                    className="px-4 py-2 rounded-xl bg-primary-600/20 border border-primary-500/40 text-primary-200 text-sm hover:bg-primary-600/30"
                  >
                    Download export
                  </button>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {selectedFinding && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-900 shadow-xl max-h-[85vh] flex flex-col">
            <div className="flex items-start justify-between gap-3 p-4 border-b border-slate-800">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">{selectedFinding.rule_id}</p>
                <h4 className="text-lg font-semibold text-white pr-6">{selectedFinding.title}</h4>
              </div>
              <button
                type="button"
                aria-label="Close"
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                onClick={() => setSelectedFinding(null)}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto text-sm text-slate-300 space-y-4">
              <p>{selectedFinding.description}</p>
              <div>
                <p className="text-xs font-semibold text-slate-500 mb-1">Evidence</p>
                <pre className="text-[11px] font-mono bg-slate-950 rounded-lg p-3 overflow-x-auto text-slate-400">
                  {JSON.stringify(selectedFinding.evidence_json, null, 2)}
                </pre>
              </div>
              {selectedFinding.remediation_json && (
                <div>
                  <p className="text-xs font-semibold text-slate-500 mb-1">Remediation</p>
                  <pre className="text-[11px] font-mono bg-slate-950 rounded-lg p-3 overflow-x-auto text-slate-400">
                    {JSON.stringify(selectedFinding.remediation_json, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
