import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  BookOpen,
  CalendarCheck,
  CalendarDays,
  Megaphone,
  Wallet,
  User,
  LogOut,
  Sprout,
} from 'lucide-react'
import { useAuth } from '../lib/AuthContext'

const navItems = [
  { to: '/', label: 'Início', icon: LayoutDashboard },
  { to: '/boletim', label: 'Boletim', icon: BookOpen },
  { to: '/frequencia', label: 'Frequência', icon: CalendarCheck },
  { to: '/financeiro', label: 'Financeiro', icon: Wallet },
  { to: '/calendario', label: 'Calendário', icon: CalendarDays },
  { to: '/avisos', label: 'Avisos', icon: Megaphone },
]

export function AppLayout() {
  const { usuario, aluno, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="sticky top-0 z-20 flex items-center justify-between bg-emerald-950 px-4 py-3 text-white shadow-lg shadow-emerald-950/10">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 text-white ring-1 ring-white/20">
            <Sprout size={21} />
          </div>
          <div className="min-w-0">
            <p className="font-display text-base font-semibold leading-tight tracking-tight">
              Semeando
            </p>
            <p className="truncate text-xs leading-tight text-emerald-200/70">
              {aluno?.nome ?? usuario?.nome ?? 'Portal do Aluno'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <NavLink
            to="/perfil"
            title="Perfil"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-800 text-emerald-100 ring-1 ring-white/15 transition-colors hover:bg-emerald-700"
          >
            <User size={16} />
          </NavLink>
          <button
            onClick={handleLogout}
            title="Sair"
            className="rounded-lg p-2 text-emerald-200/60 transition-colors hover:bg-red-500/15 hover:text-red-300"
          >
            <LogOut size={16} />
          </button>
        </div>
      </header>

      <main className="flex-1 pb-24">
        <div key={location.pathname} className="animate-rise mx-auto max-w-2xl px-4 py-6">
          <Outlet />
        </div>
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-10 flex justify-center px-3 pb-3">
        <div className="flex w-full max-w-2xl rounded-2xl border border-slate-200 bg-white/90 p-1 shadow-lift backdrop-blur">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex flex-1 flex-col items-center gap-0.5 rounded-xl py-1.5 text-[11px] font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'text-slate-400 hover:text-slate-600'
                }`
              }
            >
              <Icon size={19} />
              {label}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
