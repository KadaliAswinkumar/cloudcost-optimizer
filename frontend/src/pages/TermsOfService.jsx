import { Link } from 'react-router-dom'
import { Scale } from 'lucide-react'

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-200">
      <div className="max-w-5xl mx-auto px-6 py-12 space-y-8">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 text-primary-300 text-sm font-medium uppercase tracking-wide">
            <Scale className="w-4 h-4" />
            Legal
          </div>
          <h1 className="text-3xl font-bold text-white">Terms of Service</h1>
          <p className="text-sm text-slate-400">Effective date: May 2026</p>
          <p className="text-slate-300">
            These Terms govern your access to and use of CloudCost Optimizer websites, APIs, and software services.
          </p>
        </div>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">1. Definitions and acceptance</h2>
          <p>
            By using the service, you agree to these Terms. If you use the service on behalf of an organization, you represent that you have
            authority to bind that organization.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">2. Service scope</h2>
          <p>
            CloudCost Optimizer provides analytics, optimization recommendations, and workflow tooling for cloud cost and infrastructure
            efficiency.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">3. Accounts and security</h2>
          <p>
            You are responsible for maintaining account security, credentials, and role assignments. You must promptly notify us of suspected
            unauthorized use.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">4. Customer responsibilities</h2>
          <p>
            Customers are responsible for cloud account permissions, validating recommendations before production changes, and maintaining
            compliance with internal policies.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">5. Acceptable use</h2>
          <p>
            You may not abuse the service, attempt unauthorized access, or use the platform for unlawful activity.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">6. Fees and subscriptions</h2>
          <p>
            Paid plans are billed as described in applicable order forms or pricing pages. Non-payment may result in suspension according to
            commercial terms.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">7. Intellectual property</h2>
          <p>
            The platform, source code, models, and product assets remain the intellectual property of CloudCost Optimizer unless explicitly
            licensed otherwise.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">8. Confidentiality and data</h2>
          <p>
            Each party agrees to protect the other party’s confidential information. Customer data handling is governed by the Privacy Policy
            and applicable data processing terms.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">9. Warranty disclaimer and liability</h2>
          <p>
            Service is provided on an as-is basis. Optimization outputs are decision support tools, and final infrastructure actions remain
            customer-controlled.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">10. Suspension and termination</h2>
          <p>
            Accounts may be suspended for serious misuse or legal risk. Customers may terminate with notice under commercial agreements.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">11. Governing law and contact</h2>
          <p>
            Unless otherwise agreed in writing, these Terms are governed by applicable contractual jurisdiction in your order form.
            Legal inquiries: <a className="text-primary-300 hover:text-primary-200" href="mailto:legal@cloudcostoptimizer.io">legal@cloudcostoptimizer.io</a>
          </p>
        </section>

        <Link to="/" className="inline-block text-sm text-primary-300 hover:text-primary-200">← Back to home</Link>
      </div>
    </div>
  )
}
