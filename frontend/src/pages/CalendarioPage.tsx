import { useState } from 'react'
import { Plus, Trash2, Loader2, CalendarDays } from 'lucide-react'
import { calendarioApi } from '../api/calendario'
import { turmasApi } from '../api/turmas'
import { apiErrorMessage } from '../api/client'
import { useAsyncList } from '../lib/useAsyncList'
import { useAuth } from '../lib/AuthContext'
import type {
  EventoCalendarioCreate,
  EventoCalendarioRead,
  TipoEvento,
} from '../types/calendario'
import { TIPO_EVENTO_LABELS } from '../types/calendario'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'
import { ErrorBanner } from '../components/AsyncState'

const PERIODO_DIAS = 60

const TIPO_BADGE: Record<TipoEvento, string> = {
  PROVA: 'bg-red-50 text-red-700',
  FERIADO: 'bg-sky-50 text-sky-700',
  REUNIAO: 'bg-purple-50 text-purple-700',
  EVENTO: 'bg-emerald-50 text-emerald-700',
  OUTRO: 'bg-slate-100 text-slate-600',
}

function hoje(): string {
  return new Date().toISOString().slice(0, 10)
}

function somarDias(dataIso: string, dias: number): string {
  const d = new Date(dataIso)
  d.setDate(d.getDate() + dias)
  return d.toISOString().slice(0, 10)
}

function formatarData(dataIso: string): string {
  const [ano, mes, dia] = dataIso.split('-')
  return `${dia}/${mes}/${ano}`
}

export function CalendarioPage() {
  const { usuario } = useAuth()
  const de = hoje()
  const ate = somarDias(de, PERIODO_DIAS)

  const {
    data: eventos,
    loading,
    error,
    reload,
  } = useAsyncList(() => calendarioApi.listarEventos(de, ate), [de, ate])

  const [criando, setCriando] = useState(false)
  const [excluindoId, setExcluindoId] = useState<number | null>(null)
  const [erroExclusao, setErroExclusao] = useState<string | null>(null)

  const grupos = agruparPorData(eventos)

  async function handleExcluir(evento: EventoCalendarioRead) {
    if (!confirm(`Excluir o evento "${evento.titulo}"?`)) return
    setExcluindoId(evento.id)
    setErroExclusao(null)
    try {
      await calendarioApi.removerEvento(evento.id)
      reload()
    } catch (err) {
      setErroExclusao(apiErrorMessage(err))
    } finally {
      setExcluindoId(null)
    }
  }

  const podeEditar = (evento: EventoCalendarioRead) =>
    usuario &&
    (usuario.role === 'ADMIN' ||
      usuario.role === 'SECRETARIA' ||
      evento.criado_por_user_id === usuario.id)

  return (
    <div>
      <PageHeader
        title="Calendário"
        subtitle={
          loading ? 'Carregando...' : `${eventos.length} eventos nos próximos ${PERIODO_DIAS} dias`
        }
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

      {error && <ErrorBanner message={error} />}
      {erroExclusao && <ErrorBanner message={erroExclusao} />}

      {loading ? (
        <div className="flex justify-center py-16 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : grupos.length === 0 ? (
        <p className="py-8 text-center text-slate-400">
          Nenhum evento nos próximos {PERIODO_DIAS} dias.
        </p>
      ) : (
        <div className="space-y-6">
          {grupos.map(([data, itens]) => (
            <div key={data}>
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-500">
                <CalendarDays size={14} />
                {formatarData(data)}
              </h3>
              <div className="space-y-2">
                {itens.map((evento) => (
                  <div
                    key={evento.id}
                    className="flex items-start justify-between rounded-xl border border-slate-200 bg-white p-4"
                  >
                    <div>
                      <div className="mb-1 flex items-center gap-2">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${TIPO_BADGE[evento.tipo]}`}
                        >
                          {TIPO_EVENTO_LABELS[evento.tipo]}
                        </span>
                        {evento.data_fim && evento.data_fim !== evento.data_inicio && (
                          <span className="text-xs text-slate-400">
                            até {formatarData(evento.data_fim)}
                          </span>
                        )}
                        {evento.turma_id === null && (
                          <span className="text-xs text-slate-400">· Evento geral</span>
                        )}
                      </div>
                      <h4 className="font-medium text-slate-900">{evento.titulo}</h4>
                      {evento.descricao && (
                        <p className="mt-1 text-sm text-slate-500">{evento.descricao}</p>
                      )}
                    </div>
                    {podeEditar(evento) && (
                      <button
                        onClick={() => handleExcluir(evento)}
                        disabled={excluindoId === evento.id}
                        className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                        title="Excluir evento"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {criando && (
        <EventoForm
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

function agruparPorData(
  eventos: EventoCalendarioRead[],
): [string, EventoCalendarioRead[]][] {
  const mapa = new Map<string, EventoCalendarioRead[]>()
  for (const evento of eventos) {
    const lista = mapa.get(evento.data_inicio) ?? []
    lista.push(evento)
    mapa.set(evento.data_inicio, lista)
  }
  return [...mapa.entries()].sort(([a], [b]) => a.localeCompare(b))
}

function EventoForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [titulo, setTitulo] = useState('')
  const [descricao, setDescricao] = useState('')
  const [tipo, setTipo] = useState<TipoEvento>('EVENTO')
  const [dataInicio, setDataInicio] = useState(hoje())
  const [dataFim, setDataFim] = useState('')
  const [turmaId, setTurmaId] = useState<string>('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const { data: turmas, loading: carregandoTurmas } = useAsyncList(() => turmasApi.list())

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    const payload: EventoCalendarioCreate = {
      titulo,
      descricao: descricao || null,
      data_inicio: dataInicio,
      data_fim: dataFim || null,
      tipo,
      turma_id: turmaId ? Number(turmaId) : null,
    }
    try {
      await calendarioApi.criarEvento(payload)
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
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Título</label>
          <input
            type="text"
            required
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            className="input"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Descrição</label>
          <textarea
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            className="input"
            rows={2}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
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
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Turma (opcional)
            </label>
            <select
              value={turmaId}
              onChange={(e) => setTurmaId(e.target.value)}
              disabled={carregandoTurmas}
              className="input"
            >
              <option value="">Evento geral</option>
              {turmas.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.nome}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Data início
            </label>
            <input
              type="date"
              required
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Data fim (opcional)
            </label>
            <input
              type="date"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="input"
            />
          </div>
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
