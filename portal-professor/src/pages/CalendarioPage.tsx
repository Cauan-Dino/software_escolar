import { useEffect, useState } from 'react'
import { Plus, Loader2 } from 'lucide-react'
import { calendarioApi } from '../api/calendario'
import { turmasApi } from '../api/turmas'
import { apiErrorMessage } from '../api/client'
import type { EventoCalendarioRead, TipoEvento, TurmaRead } from '../types/api'
import { TIPO_EVENTO_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'

const TIPO_COLOR: Record<TipoEvento, string> = {
  PROVA: 'bg-red-50 text-red-700',
  FERIADO: 'bg-sky-50 text-sky-700',
  REUNIAO: 'bg-purple-50 text-purple-700',
  EVENTO: 'bg-emerald-50 text-emerald-700',
  OUTRO: 'bg-slate-100 text-slate-600',
}

export function CalendarioPage() {
  const [eventos, setEventos] = useState<EventoCalendarioRead[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [criando, setCriando] = useState(false)

  function reload() {
    setLoading(true)
    setErro(null)
    calendarioApi
      .listarEventos()
      .then(setEventos)
      .catch((err) => setErro(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(reload, [])

  return (
    <div>
      <PageHeader
        title="Calendário"
        subtitle={`${eventos.length} eventos nos próximos 60 dias`}
        action={
          <button
            onClick={() => setCriando(true)}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            <Plus size={16} />
            Novo evento
          </button>
        }
      />

      {erro && (
        <p className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{erro}</p>
      )}

      {loading ? (
        <div className="flex justify-center py-16 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : (
        <div className="space-y-2">
          {eventos.map((ev) => (
            <div
              key={ev.id}
              className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4"
            >
              <div className="w-20 shrink-0 text-center">
                <p className="text-xs text-slate-400">
                  {new Date(ev.data_inicio + 'T00:00').toLocaleDateString('pt-BR', {
                    day: '2-digit',
                    month: 'short',
                  })}
                </p>
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-slate-900">{ev.titulo}</p>
                {ev.descricao && (
                  <p className="truncate text-sm text-slate-500">{ev.descricao}</p>
                )}
              </div>
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-medium ${TIPO_COLOR[ev.tipo]}`}
              >
                {TIPO_EVENTO_LABELS[ev.tipo]}
              </span>
            </div>
          ))}
          {eventos.length === 0 && (
            <p className="py-8 text-center text-slate-400">
              Nenhum evento nos próximos 60 dias.
            </p>
          )}
        </div>
      )}

      {criando && (
        <NovoEventoModal
          onClose={() => setCriando(false)}
          onSaved={() => {
            setCriando(false)
            reload()
          }}
        />
      )}
    </div>
  )
}

function NovoEventoModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [turmas, setTurmas] = useState<TurmaRead[]>([])
  const [titulo, setTitulo] = useState('')
  const [descricao, setDescricao] = useState('')
  const [tipo, setTipo] = useState<TipoEvento>('PROVA')
  const [dataInicio, setDataInicio] = useState('')
  const [turmaId, setTurmaId] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    turmasApi.minhas().then(setTurmas)
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await calendarioApi.criarEvento({
        titulo,
        descricao: descricao || null,
        data_inicio: dataInicio,
        tipo,
        turma_id: Number(turmaId),
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Novo evento" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
          Professores só criam eventos para uma turma específica em que lecionam.
        </p>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Turma</label>
          <select
            required
            value={turmaId}
            onChange={(e) => setTurmaId(e.target.value)}
            className="input"
          >
            <option value="">Selecione...</option>
            {turmas.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Título</label>
          <input
            required
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            className="input"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Tipo</label>
            <select
              value={tipo}
              onChange={(e) => setTipo(e.target.value as TipoEvento)}
              className="input"
            >
              {Object.entries(TIPO_EVENTO_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Data</label>
            <input
              type="date"
              required
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="input"
            />
          </div>
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Descrição (opcional)
          </label>
          <textarea
            rows={3}
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            className="input"
          />
        </div>

        {erro && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>}

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
