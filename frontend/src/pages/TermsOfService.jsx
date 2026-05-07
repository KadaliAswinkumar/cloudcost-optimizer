import { Link } from 'react-router-dom'

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-200">
      <div className="max-w-4xl mx-auto px-6 py-12 space-y-6">
        <h1 className="text-3xl font-bold text-white">Terms of Service</h1>
        <p className="text-sm text-slate-400">Last updated: May 2026</p>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">1. Service scope</h2>
          <p>
            CloudCost Optimizer provides analytics, optimization recommendations, and workflow tooling for cloud cost and infrastructure
            efficiency.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">2. Customer responsibilities</h2>
          <p>
            Customers are responsible for cloud account permissions, validating recommendations before production changes, and maintaining
            compliance with internal policies.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">3. Acceptable use</h2>
          <p>
            You may not abuse the service, attempt unauthorized access, or use the platform for unlawful activity.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">4. Intellectual property</h2>
          <p>
            The platform, source code, models, and product assets remain the intellectual property of CloudCost Optimizer unless explicitly
            licensed otherwise.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">5. Warranty and liability</h2>
          <p>
            Service is provided on an as-is basis. Optimization outputs are decision support tools, and final infrastructure actions remain
            customer-controlled.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">6. Termination</h2>
          <p>
            Accounts may be suspended for serious misuse or legal risk. Customers may terminate with notice under commercial agreements.
          </p>
        </section>

        <p className="text-slate-400">
          Contract and legal inquiries: <a className="text-primary-300 hover:text-primary-200" href="mailto:legal@cloudcostoptimizer.io">legal@cloudcostoptimizer.io</a>
        </p>
        <Link to="/" className="inline-block text-sm text-primary-300 hover:text-primary-200">← Back to home</Link>
      </div>
    </div>
  )
}
