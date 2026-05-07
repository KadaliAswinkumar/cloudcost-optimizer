import { Link } from 'react-router-dom'

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-200">
      <div className="max-w-4xl mx-auto px-6 py-12 space-y-6">
        <h1 className="text-3xl font-bold text-white">Privacy Policy</h1>
        <p className="text-sm text-slate-400">Last updated: May 2026</p>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">1. What we collect</h2>
          <p>
            We collect account details (name, email), billing and infrastructure metadata you connect, and operational logs required to run,
            secure, and improve the product.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">2. How we use data</h2>
          <p>
            We use connected data to provide cost analysis, infrastructure recommendations, anomaly detection, and investor reporting within
            your account context.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">3. Data retention and security</h2>
          <p>
            We retain data only as long as needed for service delivery and legal obligations. We apply role-based access, encrypted transport,
            and encrypted storage controls for sensitive connector details.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">4. Data sharing</h2>
          <p>
            We do not sell customer data. We may share limited data with infrastructure sub-processors required to operate the service.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-xl font-semibold text-white">5. Your rights</h2>
          <p>
            You can request data export, correction, and deletion by contacting support. Enterprise customers may execute a DPA as part of
            procurement.
          </p>
        </section>

        <p className="text-slate-400">
          Questions: <a className="text-primary-300 hover:text-primary-200" href="mailto:support@cloudcostoptimizer.io">support@cloudcostoptimizer.io</a>
        </p>
        <Link to="/" className="inline-block text-sm text-primary-300 hover:text-primary-200">← Back to home</Link>
      </div>
    </div>
  )
}
