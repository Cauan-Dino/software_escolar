import { NavLink, Outlet, useNavigate } from 'react-router-dom'
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
} from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../lib/AuthContext'
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
  const { filhos, filhoAtivo, selecionarFilho } = useFilho()
  const navigate = useNavigate()
  const [seletorAberto, setSeletorAberto] = useState(false)

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="flex w-60 flex-col border-r border-slate-200 bg-white">
        <div className="flex items-center gap-2 px-6 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 text-white">
            <Sprout size={20} />
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight text-slate-900">Semeando</p>
            <p className="text-xs leading-tight text-slate-400">Portal do Responsável</p>
          </div>
        </div>

        {filhos.length > 0 && (
          <div className="relative mx-3 mb-2">
            <button
              onClick={() => setSeletorAberto((v) => !v)}
              className="flex w-full items-center justify-between gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-100"
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

        <nav className="flex-1 space-y-1 px-3 py-2">
          {navItems.map(({ to, label, icon: Icon }) => (
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
                <p className="truncate text-sm font-medium text-slate-900">{usuario?.nome}</p>
                <p className="truncate text-xs text-slate-400">{usuario?.email}</p>
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
        <div className="mx-auto max-w-5xl px-8 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
