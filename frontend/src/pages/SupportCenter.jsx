import { Link } from 'react-router-dom'
import { LifeBuoy, Mail, ShieldCheck } from 'lucide-react'

export default function SupportCenter() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-200">
      <div className="max-w-5xl mx-auto px-6 py-12 space-y-8">
        <div>
          <div className="inline-flex items-center gap-2 text-primary-300 text-sm font-medium uppercase tracking-wide">
            <LifeBuoy className="w-4 h-4" />
            Support
          </div>
          <h1 className="text-3xl font-bold text-white mt-2">Support Center</h1>
          <p className="text-slate-400 mt-2">Technical support, onboarding help, and issue escalation details.</p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
            <div className="flex items-center gap-2 text-emerald-300 mb-2">
              <Mail className="w-4 h-4" />
              <h2 className="font-semibold text-white">Email support</h2>
            </div>
            <p className="text-slate-300 text-sm">General, onboarding, and product support</p>
            <a className="text-primary-300 hover:text-primary-200 text-sm" href="mailto:support@cloudcostoptimizer.io">
              support@cloudcostoptimizer.io
            </a>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
            <div className="flex items-center gap-2 text-sky-300 mb-2">
              <ShieldCheck className="w-4 h-4" />
              <h2 className="font-semibold text-white">Security contacts</h2>
            </div>
            <p className="text-slate-300 text-sm">Responsible disclosure and urgent security communication</p>
            <a className="text-primary-300 hover:text-primary-200 text-sm" href="mailto:security@cloudcostoptimizer.io">
              security@cloudcostoptimizer.io
            </a>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
          <h2 className="text-xl font-semibold text-white">Suggested support policy</h2>
          <ul className="list-disc pl-5 mt-3 space-y-1 text-slate-300">
            <li>P1 critical outage: first response within 1 hour.</li>
            <li>P2 degraded functionality: first response within 4 business hours.</li>
            <li>P3 standard issues and requests: first response within 1 business day.</li>
            <li>Onboarding support: weekly guided optimization reviews.</li>
          </ul>
        </div>

        <Link to="/" className="inline-block text-sm text-primary-300 hover:text-primary-200">← Back to home</Link>
      </div>
    </div>
  )
}
