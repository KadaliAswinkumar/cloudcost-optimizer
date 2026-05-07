import { Link, useLocation, useNavigate } from 'react-router-dom'
import { 
  Cloud, 
  LayoutDashboard, 
  Sparkles, 
  Search, 
  GitCompare, 
  Calculator,
  Menu,
  X,
  Zap,
  LogOut,
  User,
  RadioTower,
  PieChart,
  Gauge,
} from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Cost Intelligence (FinOps)', href: '/finops', icon: PieChart },
  { name: 'Savings Readiness', href: '/readiness', icon: Gauge },
  { name: 'Infrastructure Intelligence', href: '/infra-intelligence', icon: RadioTower },
  { name: 'CloudCost AI™', href: '/ai', icon: Sparkles },
  { name: 'Spot Intelligence™', href: '/spot-intelligence', icon: Zap },
  { name: 'Get Recommendations', href: '/recommendations', icon: Sparkles },
  { name: 'Find Instances', href: '/instances', icon: Search },
  { name: 'Compare Clouds', href: '/compare', icon: GitCompare },
  { name: 'Cost Calculator', href: '/calculator', icon: Calculator },
]

export default function Layout({ children }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Background gradient effect */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
      </div>

      {/* Sidebar - Desktop */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-72 lg:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-slate-900/50 backdrop-blur-xl border-r border-slate-800/50 px-6 pb-4">
          {/* Logo */}
          <div className="flex h-20 shrink-0 items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 shadow-lg shadow-primary-500/25">
              <Cloud className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">CloudCost</h1>
              <p className="text-xs text-slate-400">Multi-Cloud Optimizer</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col gap-y-2">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <li key={item.name}>
                    <Link
                      to={item.href}
                      className={`
                        group flex gap-x-3 rounded-xl p-3 text-sm font-medium transition-all duration-200 relative
                        ${isActive 
                          ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20' 
                          : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                        }
                      `}
                    >
                      <item.icon className={`w-5 h-5 shrink-0 ${isActive ? 'text-primary-400' : 'text-slate-500 group-hover:text-white'}`} />
                      {item.name}
                    </Link>
                  </li>
                )
              })}
            </ul>

            {/* Cloud provider badges */}
            <div className="mt-auto pt-4 border-t border-slate-800">
              {/* User Profile */}
              <div className="mb-4 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                    <User className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {user?.name || 'User'}
                    </p>
                    <p className="text-xs text-slate-500 truncate">
                      {user?.email || ''}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300 hover:text-white text-sm font-medium transition-all"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>

              <p className="text-xs text-slate-500 mb-3">Supported Clouds</p>
              <div className="flex gap-2">
                <span className="px-2.5 py-1 text-xs font-medium bg-aws/10 text-aws rounded-lg border border-aws/20">
                  AWS
                </span>
                <span className="px-2.5 py-1 text-xs font-medium bg-gcp/10 text-gcp rounded-lg border border-gcp/20">
                  GCP
                </span>
                <span className="px-2.5 py-1 text-xs font-medium bg-azure/10 text-azure rounded-lg border border-azure/20">
                  Azure
                </span>
              </div>
            </div>
          </nav>
        </div>
      </aside>

      {/* Mobile header */}
      <div className="sticky top-0 z-40 flex items-center gap-x-6 bg-slate-900/80 backdrop-blur-xl px-4 py-4 shadow-sm sm:px-6 lg:hidden border-b border-slate-800/50">
        <button
          type="button"
          className="-m-2.5 p-2.5 text-slate-400 lg:hidden"
          onClick={() => setMobileMenuOpen(true)}
        >
          <Menu className="h-6 w-6" />
        </button>
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600">
            <Cloud className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-semibold text-white">CloudCost</span>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)} />
          <div className="fixed inset-y-0 left-0 w-full max-w-xs bg-slate-900 p-6">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-2">
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600">
                  <Cloud className="w-6 h-6 text-white" />
                </div>
                <span className="text-xl font-bold text-white">CloudCost</span>
              </div>
              <button onClick={() => setMobileMenuOpen(false)} className="text-slate-400">
                <X className="w-6 h-6" />
              </button>
            </div>
            <nav className="flex flex-col gap-2">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`
                      flex gap-x-3 rounded-xl p-3 text-sm font-medium
                      ${isActive 
                        ? 'bg-primary-500/10 text-primary-400' 
                        : 'text-slate-400 hover:bg-slate-800'
                      }
                    `}
                  >
                    <item.icon className="w-5 h-5" />
                    {item.name}
                  </Link>
                )
              })}

              {/* Logout button in mobile menu */}
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 px-3 py-3 mt-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-sm font-medium transition-all border-t border-slate-800 pt-6"
              >
                <LogOut className="w-5 h-5" />
                Sign Out
              </button>
            </nav>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="lg:pl-72">
        <div className="px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  )
}

