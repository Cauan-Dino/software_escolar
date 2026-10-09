import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sprout, Loader2 } from 'lucide-react'
import { useAuth } from '../lib/AuthContext'
import { apiErrorMessage } from '../api/client'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setErro(null)
    try {
      await login(email, senha)
      navigate('/')
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      <aside className="relative hidden overflow-hidden bg-emerald-950 lg:block">
        <div className="absolute -left-24 -top-24 h-96 w-96 rounded-full bg-emerald-700/40 blur-3xl" />
        <div className="absolute -bottom-32 right-0 h-[28rem] w-[28rem] rounded-full bg-emerald-500/20 blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)',
            backgroundSize: '28px 28px',
          }}
        />
        <div className="relative flex h-full flex-col justify-between p-14 text-white">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-lg shadow-emerald-950/50 ring-1 ring-white/20">
              <Sprout size={24} />
            </div>
            <span className="font-display text-2xl font-semibold tracking-tight">Semeando</span>
          </div>
          <div>
            <h2 className="font-display max-w-md text-4xl font-semibold leading-tight tracking-tight">
              Suas notas, faltas e avisos em um só lugar.
            </h2>
            <p className="mt-5 max-w-sm text-sm leading-relaxed text-emerald-100/70">
              Acompanhe seu boletim, sua frequência e os comunicados da escola de forma simples e rápida.
            </p>
          </div>
          <p className="text-xs text-emerald-200/40">Semeando · Portal do Aluno</p>
        </div>
      </aside>

      <div className="flex items-center justify-center bg-slate-50 px-6 py-12">
        <div className="animate-rise w-full max-w-sm">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-lg shadow-emerald-600/30">
              <Sprout size={22} />
            </div>
            <span className="font-display text-xl font-semibold text-slate-900">Semeando</span>
          </div>

          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-700">
            Portal do Aluno
          </p>
          <h1 className="font-display mt-2 text-3xl font-semibold tracking-tight text-slate-900">
            Bem-vindo de volta
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Entre com suas credenciais para acessar o portal.
          </p>

          <form onSubmit={handleSubmit} className="mt-8">
            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">E-mail</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input"
                  placeholder="voce@semeando.edu.br"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">Senha</label>
                <input
                  type="password"
                  required
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  className="input"
                />
              </div>
            </div>

            {erro && (
              <p className="mt-4 rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700">
                {erro}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-700 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-900/20 transition-all hover:bg-emerald-800 hover:shadow-emerald-900/30 disabled:opacity-60"
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              Entrar
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
