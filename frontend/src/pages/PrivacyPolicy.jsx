import { Link } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-200">
      <div className="max-w-5xl mx-auto px-6 py-12 space-y-8">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 text-primary-300 text-sm font-medium uppercase tracking-wide">
            <ShieldCheck className="w-4 h-4" />
            Trust Center
          </div>
          <h1 className="text-3xl font-bold text-white">Privacy Policy</h1>
          <p className="text-sm text-slate-400">Effective date: May 2026</p>
          <p className="text-slate-300">
            This Privacy Policy explains how CloudCost Optimizer collects, uses, stores, and protects information
            when customers use our website, APIs, and SaaS platform.
          </p>
        </div>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">1. Scope and role</h2>
          <p>CloudCost Optimizer acts as a service provider/data processor for customer cloud and billing data processed through the platform.</p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">2. Information we collect</h2>
          <ul className="list-disc pl-6 space-y-1 text-slate-300">
            <li>Account data: name, email, organization, authentication metadata.</li>
            <li>Product data: recommendation states, action events, onboarding metadata, anomaly records.</li>
            <li>Connected cloud/billing data: usage, pricing, inventory, and cost metrics required for analysis.</li>
            <li>Operational telemetry: logs, diagnostics, and support records.</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">3. Purpose of processing</h2>
          <ul className="list-disc pl-6 space-y-1 text-slate-300">
            <li>Deliver product functionality including dashboards, recommendations, scoring, anomalies, and reports.</li>
            <li>Secure the platform and prevent abuse, unauthorized access, and fraud.</li>
            <li>Provide customer support, onboarding assistance, and service reliability improvements.</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">4. Legal basis and customer control</h2>
          <p>
            Customers determine what sources to connect and remain responsible for data they provide. We process that data under customer
            instruction and applicable law, including contractual necessity and legitimate interest in secure service operations.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">5. Data sharing and subprocessors</h2>
          <p>
            We do not sell personal data. We may use vetted subprocessors for hosting, monitoring, and support infrastructure. Subprocessors
            are contractually bound to confidentiality and security obligations.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">6. Security and retention</h2>
          <ul className="list-disc pl-6 space-y-1 text-slate-300">
            <li>Encryption in transit and security controls for sensitive credentials.</li>
            <li>Access restrictions and role-based controls for operations.</li>
            <li>Retention only as needed for service, legal, and operational continuity obligations.</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">7. Your rights</h2>
          <p>
            Subject to law and contract, customers may request data export, correction, and deletion. Data processing terms may be executed
            for enterprise engagements.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">8. Contact and updates</h2>
          <p>
            Privacy inquiries: <a className="text-primary-300 hover:text-primary-200" href="mailto:privacy@cloudcostoptimizer.io">privacy@cloudcostoptimizer.io</a>
          </p>
          <p>We may update this policy periodically. Material updates are reflected with a revised effective date.</p>
        </section>

        <Link to="/" className="inline-block text-sm text-primary-300 hover:text-primary-200">← Back to home</Link>
      </div>
    </div>
  )
}
