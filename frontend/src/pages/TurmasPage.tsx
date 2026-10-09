import { useState } from 'react'
import { Plus, Users, GraduationCap, Loader2, AlertTriangle } from 'lucide-react'
import { turmasApi } from '../api/turmas'
import { apiErrorMessage } from '../api/client'
import { useAsyncList } from '../lib/useAsyncList'
import type { Serie, TurmaCreate, TurmaRead, Turno } from '../types/api'
import { SERIE_LABELS, TURNO_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'

export function TurmasPage() {
  const { data: turmas, loading, error, reload } = useAsyncList(() => turmasApi.list())
  const [criando, setCriando] = useState(false)
  const [editando, setEditando] = useState<TurmaRead | null>(null)

  return (
    <div>
      <PageHeader
        title="Turmas"
        subtitle={loading ? 'Carregando...' : `${turmas.length} turmas cadastradas`}
        action={
          <button
            onClick={() => setCriando(true)}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            <Plus size={16} />
            Nova turma
          </button>
        }
      />

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {turmas.map((t) => {
            const pct = Math.round((t.vagas_ocupadas / t.capacidade) * 100)
            return (
              <button
                key={t.id}
                onClick={() => setEditando(t)}
                className="rounded-xl border border-slate-200 bg-white p-5 text-left transition-shadow hover:shadow-md"
              >
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-50 text-sky-600">
                    <GraduationCap size={20} />
                  </div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                    {TURNO_LABELS[t.turno]}
                  </span>
                </div>
                <h3 className="font-semibold text-slate-900">{t.nome}</h3>
                <p className="mb-3 text-xs text-slate-400">
                  Ano letivo {t.ano_letivo} {!t.ativa && '· Inativa'}
                </p>

                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="flex items-center gap-1.5 text-slate-500">
                    <Users size={14} />
                    {t.vagas_ocupadas}/{t.capacidade}
                  </span>
                  <span className="text-slate-400">{pct}%</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full ${
                      pct >= 100 ? 'bg-red-400' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(pct, 100)}%` }}
                  />
                </div>

                {t.professores.length > 0 && (
                  <p className="mt-3 truncate text-xs text-slate-500">
                    Prof.: {t.professores.map((p) => p.nome).join(', ')}
                  </p>
                )}
              </button>
            )
          })}
          {turmas.length === 0 && (
            <p className="col-span-full py-8 text-center text-slate-400">
              Nenhuma turma cadastrada.
            </p>
          )}
        </div>
      )}

      {criando && (
        <TurmaForm
          onClose={() => setCriando(false)}
          onSaved={() => {
            setCriando(false)
            reload()
          }}
        />
      )}
      {editando && (
        <TurmaEditForm
          turma={editando}
          onClose={() => setEditando(null)}
          onSaved={() => {
            setEditando(null)
            reload()
          }}
        />
      )}
    </div>
  )
}

function TurmaForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [serie, setSerie] = useState<Serie>('ANO_1')
  const [turno, setTurno] = useState<Turno>('MANHA')
  const [anoLetivo, setAnoLetivo] = useState(new Date().getFullYear())
  const [capacidade, setCapacidade] = useState(25)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    const payload: TurmaCreate = { serie, turno, ano_letivo: anoLetivo, capacidade }
    try {
      await turmasApi.create(payload)
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Nova turma" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Série
          </label>
          <select
            value={serie}
            onChange={(e) => setSerie(e.target.value as Serie)}
            className="input"
          >
            {Object.entries(SERIE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Turno
            </label>
            <select
              value={turno}
              onChange={(e) => setTurno(e.target.value as Turno)}
              className="input"
            >
              {Object.entries(TURNO_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Ano letivo
            </label>
            <input
              type="number"
              required
              value={anoLetivo}
              onChange={(e) => setAnoLetivo(Number(e.target.value))}
              className="input"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Capacidade
            </label>
            <input
              type="number"
              required
              min={1}
              max={30}
              value={capacidade}
              onChange={(e) => setCapacidade(Number(e.target.value))}
              className="input"
            />
          </div>
        </div>

        {erro && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={salvando}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {salvando ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function TurmaEditForm({
  turma,
  onClose,
  onSaved,
}: {
  turma: TurmaRead
  onClose: () => void
  onSaved: () => void
}) {
  const [capacidade, setCapacidade] = useState(turma.capacidade)
  const [ativa, setAtiva] = useState(turma.ativa)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await turmasApi.update(turma.id, { capacidade, ativa })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title={`Editar ${turma.nome}`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Capacidade
          </label>
          <input
            type="number"
            required
            min={1}
            max={30}
            value={capacidade}
            onChange={(e) => setCapacidade(Number(e.target.value))}
            className="input"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={ativa}
            onChange={(e) => setAtiva(e.target.checked)}
            className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
          />
          Turma ativa
        </label>

        {erro && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={salvando}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {salvando ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
