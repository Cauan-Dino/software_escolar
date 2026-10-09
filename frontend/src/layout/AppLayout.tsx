import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  GraduationCap,
  Users2,
  ClipboardList,
  LogOut,
  Sprout,
  UserCog,
  Briefcase,
  ShieldCheck,
  BookOpen,
  CalendarCheck,
  CalendarDays,
  Megaphone,
  Wallet,
} from 'lucide-react'
import { useAuth } from '../lib/AuthContext'

const navGroups = [
  {
    items: [{ to: '/', label: 'Dashboard', icon: LayoutDashboard }],
  },
  {
    title: 'Pessoas',
    items: [
      { to: '/alunos', label: 'Alunos', icon: Users2 },
      { to: '/responsaveis', label: 'Responsáveis', icon: UserCog },
      { to: '/professores', label: 'Professores', icon: GraduationCap },
      { to: '/funcionarios', label: 'Funcionários', icon: Briefcase },
    ],
  },
  {
    title: 'Acadêmico',
    items: [
      { to: '/turmas', label: 'Turmas', icon: GraduationCap },
      { to: '/matriculas', label: 'Matrículas', icon: ClipboardList },
      { to: '/notas', label: 'Notas', icon: BookOpen },
      { to: '/frequencia', label: 'Frequência', icon: CalendarCheck },
      { to: '/calendario', label: 'Calendário', icon: CalendarDays },
    ],
  },
  {
    title: 'Escola',
    items: [
      { to: '/comunicacao', label: 'Comunicação', icon: Megaphone },
      { to: '/financeiro', label: 'Financeiro', icon: Wallet },
    ],
  },
  {
    title: 'Administração',
    items: [{ to: '/usuarios', label: 'Usuários', icon: ShieldCheck }],
  },
]

export function AppLayout() {
  const { usuario, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="flex w-64 flex-col border-r border-slate-200 bg-white">
        <div className="flex items-center gap-2 px-6 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 text-white">
            <Sprout size={20} />
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight text-slate-900">
              Semeando
            </p>
            <p className="text-xs leading-tight text-slate-400">
              Gestão Escolar
            </p>
          </div>
        </div>

        <nav className="flex-1 space-y-4 overflow-y-auto px-3 py-2">
          {navGroups.map((group, i) => (
            <div key={i}>
              {group.title && (
                <p className="px-3 pb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  {group.title}
                </p>
              )}
              <div className="space-y-1">
                {group.items.map(({ to, label, icon: Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-emerald-50 text-emerald-700'
                          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                      }`
                    }
                  >
                    <Icon size={18} />
                    {label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-slate-200 p-3">
          <div className="flex items-center gap-3 rounded-lg px-3 py-2">
            <NavLink
              to="/perfil"
              className="flex min-w-0 flex-1 items-center gap-3 rounded-lg hover:bg-slate-100"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-200 text-sm font-semibold text-slate-700">
                {usuario?.nome.charAt(0) ?? '?'}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-900">
                  {usuario?.nome}
                </p>
                <p className="truncate text-xs text-slate-400">
                  {usuario?.email}
                </p>
              </div>
            </NavLink>
            <button
              onClick={handleLogout}
              title="Sair"
              className="rounded-md p-2 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-8 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
