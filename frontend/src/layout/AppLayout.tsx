import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
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
  Menu,
  X,
} from 'lucide-react'
import { useAuth } from '../lib/AuthContext'
import { ChatAssistente, EVENTO_ACAO_CONFIRMADA } from '../components/ChatAssistente'

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
  const location = useLocation()
  const [menuAberto, setMenuAberto] = useState(false)
  // Sobe quando o assistente executa uma ação: remonta a página atual para recarregar os dados.
  const [versaoDados, setVersaoDados] = useState(0)

  useEffect(() => {
    const aoConfirmar = () => setVersaoDados((v) => v + 1)
    window.addEventListener(EVENTO_ACAO_CONFIRMADA, aoConfirmar)
    return () => window.removeEventListener(EVENTO_ACAO_CONFIRMADA, aoConfirmar)
  }, [])

  useEffect(() => {
    setMenuAberto(false)
  }, [location.pathname])

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const iniciais =
    usuario?.nome
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0])
      .join('')
      .toUpperCase() ?? '?'

  return (
    <div className="flex min-h-screen bg-slate-50">
      {menuAberto && (
        <div
          className="fixed inset-0 z-30 bg-emerald-950/50 backdrop-blur-[2px] lg:hidden"
          onClick={() => setMenuAberto(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-emerald-950 text-emerald-50 transition-transform duration-200 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${
          menuAberto ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-3 px-6 pb-4 pt-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 text-white shadow-lg shadow-emerald-950/40 ring-1 ring-white/20">
            <Sprout size={22} />
          </div>
          <div className="flex-1">
            <p className="font-display text-lg font-semibold leading-tight tracking-tight text-white">
              Semeando
            </p>
            <p className="text-[11px] uppercase leading-tight tracking-[0.14em] text-emerald-300/70">
              Gestão Escolar
            </p>
          </div>
          <button
            onClick={() => setMenuAberto(false)}
            className="rounded-md p-1 text-emerald-200/70 hover:bg-white/10 lg:hidden"
            aria-label="Fechar menu"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-scroll flex-1 space-y-5 overflow-y-auto px-3 py-4">
          {navGroups.map((group, i) => (
            <div key={i}>
              {group.title && (
                <p className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-300/50">
                  {group.title}
                </p>
              )}
              <div className="space-y-0.5">
                {group.items.map(({ to, label, icon: Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    className={({ isActive }) =>
                      `group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-white/10 text-white'
                          : 'text-emerald-100/70 hover:bg-white/5 hover:text-white'
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <span className="absolute -left-3 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-emerald-400" />
                        )}
                        <Icon
                          size={17}
                          className={
                            isActive
                              ? 'text-emerald-300'
                              : 'text-emerald-300/50 group-hover:text-emerald-300'
                          }
                        />
                        {label}
                      </>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-white/10 p-3">
          <div className="flex items-center gap-1 rounded-xl p-1.5">
            <NavLink
              to="/perfil"
              className="flex min-w-0 flex-1 items-center gap-3 rounded-lg p-1.5 transition-colors hover:bg-white/5"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-800 text-xs font-semibold text-emerald-100 ring-1 ring-white/15">
                {iniciais}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-white">
                  {usuario?.nome}
                </p>
                <p className="truncate text-xs text-emerald-200/50">
                  {usuario?.email}
                </p>
              </div>
            </NavLink>
            <button
              onClick={handleLogout}
              title="Sair"
              className="rounded-lg p-2 text-emerald-200/50 transition-colors hover:bg-red-500/15 hover:text-red-300"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-slate-200 bg-slate-50/85 px-4 py-3 backdrop-blur lg:hidden">
          <button
            onClick={() => setMenuAberto(true)}
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"
            aria-label="Abrir menu"
          >
            <Menu size={20} />
          </button>
          <span className="font-display text-base font-semibold text-slate-900">
            Semeando
          </span>
        </header>

        <main className="flex-1">
          <div key={`${location.pathname}-${versaoDados}`} className="animate-rise mx-auto max-w-6xl px-5 py-8 lg:px-10 lg:py-10">
            <Outlet />
          </div>
        </main>
      </div>
      <ChatAssistente />
    </div>
  )
}
