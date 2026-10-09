import { NavLink, Outlet, useNavigate } from 'react-router-dom'
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

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 text-white">
            <Sprout size={20} />
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight text-slate-900">Semeando</p>
            <p className="text-xs leading-tight text-slate-400">
              {aluno?.nome ?? usuario?.nome ?? 'Portal do Aluno'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <NavLink
            to="/perfil"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 text-sm font-semibold text-slate-700"
          >
            <User size={16} />
          </NavLink>
          <button
            onClick={handleLogout}
            title="Sair"
            className="rounded-md p-2 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
          >
            <LogOut size={16} />
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto pb-20">
        <div className="mx-auto max-w-2xl px-4 py-6">
          <Outlet />
        </div>
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-10 flex border-t border-slate-200 bg-white">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-medium transition-colors ${
                isActive ? 'text-emerald-600' : 'text-slate-400 hover:text-slate-600'
              }`
            }
          >
            <Icon size={20} />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
