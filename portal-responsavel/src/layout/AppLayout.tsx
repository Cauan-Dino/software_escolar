import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  BookOpen,
  CalendarCheck,
  CalendarDays,
  Megaphone,
  Wallet,
  ClipboardList,
  LogOut,
  Sprout,
  ChevronDown,
  Menu,
  X,
} from 'lucide-react'
import { useAuth } from '../lib/AuthContext'
import { InstallButton } from '../components/InstallButton'
import { useFilho } from '../lib/FilhoContext'

const navItems = [
  { to: '/', label: 'Início', icon: LayoutDashboard },
  { to: '/boletim', label: 'Boletim', icon: BookOpen },
  { to: '/frequencia', label: 'Frequência', icon: CalendarCheck },
  { to: '/financeiro', label: 'Financeiro', icon: Wallet },
  { to: '/matricula', label: 'Matrícula', icon: ClipboardList },
  { to: '/comunicacao', label: 'Mural', icon: Megaphone },
  { to: '/calendario', label: 'Calendário', icon: CalendarDays },
]

export function AppLayout() {
  const { usuario, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuAberto, setMenuAberto] = useState(false)
  const { filhos, filhoAtivo, selecionarFilho } = useFilho()
  const [seletorAberto, setSeletorAberto] = useState(false)

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
              Portal do Responsável
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

        {filhos.length > 0 && (
          <div className="relative mx-3 mb-2">
            <button
              onClick={() => setSeletorAberto((v) => !v)}
              className="flex w-full items-center justify-between gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-left text-sm font-medium text-emerald-50 transition-colors hover:bg-white/10"
            >
              <span className="truncate">{filhoAtivo?.nome ?? 'Selecione um filho'}</span>
              {filhos.length > 1 && <ChevronDown size={14} className="shrink-0" />}
            </button>
            {seletorAberto && filhos.length > 1 && (
              <div className="absolute left-0 right-0 top-full z-10 mt-1 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg">
                {filhos.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => {
                      selecionarFilho(f.id)
                      setSeletorAberto(false)
                    }}
                    className={`block w-full px-3 py-2 text-left text-sm hover:bg-slate-50 ${
                      f.id === filhoAtivo?.id
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'text-slate-700'
                    }`}
                  >
                    {f.nome}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
          {navItems.map(({ to, label, icon: Icon }) => (
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
        </nav>

        <InstallButton />

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
                <p className="truncate text-sm font-medium text-white">{usuario?.nome}</p>
                <p className="truncate text-xs text-emerald-200/50">{usuario?.email}</p>
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
          <span className="font-display text-base font-semibold text-slate-900">Semeando</span>
        </header>

        <main className="flex-1">
          <div
            key={location.pathname}
            className="animate-rise mx-auto max-w-5xl px-5 py-8 lg:px-10 lg:py-10"
          >
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
