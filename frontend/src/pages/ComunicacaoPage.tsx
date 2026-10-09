import { useEffect, useState } from 'react'
import { Pin, Plus } from 'lucide-react'
import { comunicacaoApi } from '../api/comunicacao'
import { turmasApi } from '../api/turmas'
import { apiErrorMessage } from '../api/client'
import { useAuth } from '../lib/AuthContext'
import { usePaginatedList } from '../lib/usePaginatedList'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'
import { ErrorBanner } from '../components/AsyncState'
import { Pagination } from '../components/Pagination'
import type { AvisoRead, PublicoAlvo } from '../types/comunicacao'
import { PUBLICO_ALVO_LABELS } from '../types/comunicacao'
import type { TurmaRead } from '../types/api'

const PUBLICO_STYLE: Record<PublicoAlvo, string> = {
  TODOS: 'bg-slate-100 text-slate-600',
  TURMA: 'bg-sky-50 text-sky-700',
  RESPONSAVEIS: 'bg-amber-50 text-amber-700',
  PROFESSORES: 'bg-emerald-50 text-emerald-700',
}

export function ComunicacaoPage() {
  const { usuario } = useAuth()
  const {
    data: avisos,
    total,
    loading,
    error,
    reload,
    offset,
    pageSize,
    hasPrev,
    hasNext,
    goPrev,
    goNext,
  } = usePaginatedList<AvisoRead>((params) => comunicacaoApi.listarAvisos(params))
  const [criando, setCriando] = useState(false)

  const podeCriar =
    usuario?.role === 'ADMIN' || usuario?.role === 'SECRETARIA' || usuario?.role === 'PROFESSOR'

  async function handleAbrirAviso(aviso: AvisoRead) {
    if (!aviso.lido) {
      try {
        await comunicacaoApi.marcarLido(aviso.id)
        reload()
      } catch {
        // ignora falha ao marcar leitura; não bloqueia a visualização
      }
    }
  }

  return (
    <div>
      <PageHeader
        title="Mural de avisos"
        subtitle={loading ? 'Carregando...' : `${total} aviso(s)`}
        action={
          podeCriar && (
            <button
              onClick={() => setCriando(true)}
              className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
            >
              <Plus size={16} />
              Novo aviso
            </button>
          )
        }
      />

      {error && <ErrorBanner message={error} />}

      <div className="space-y-3">
        {loading && (
          <div className="rounded-xl border border-slate-200 bg-white px-5 py-10 text-center text-slate-400">
            Carregando...
          </div>
        )}
        {!loading && !error && avisos.length === 0 && (
          <div className="rounded-xl border border-slate-200 bg-white px-5 py-10 text-center text-slate-400">
            Nenhum aviso publicado ainda.
          </div>
        )}
        {!loading &&
          !error &&
          avisos.map((aviso) => (
            <button
              key={aviso.id}
              onClick={() => handleAbrirAviso(aviso)}
              className="block w-full rounded-xl border border-slate-200 bg-white px-5 py-4 text-left hover:bg-slate-50"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  {aviso.fixado && <Pin size={14} className="text-emerald-600" />}
                  <h3 className="font-semibold text-slate-900">{aviso.titulo}</h3>
                  {!aviso.lido && (
                    <span className="rounded-full bg-emerald-600 px-2 py-0.5 text-[10px] font-medium uppercase text-white">
                      Novo
                    </span>
                  )}
                </div>
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${PUBLICO_STYLE[aviso.publico_alvo]}`}
                >
                  {PUBLICO_ALVO_LABELS[aviso.publico_alvo]}
                </span>
              </div>
              <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{aviso.corpo}</p>
              <p className="mt-3 text-xs text-slate-400">
                {new Date(aviso.publicado_em).toLocaleString('pt-BR')}
              </p>
            </button>
          ))}
      </div>

      <Pagination
        offset={offset}
        pageSize={pageSize}
        total={total}
        hasPrev={hasPrev}
        hasNext={hasNext}
        onPrev={goPrev}
        onNext={goNext}
      />

      {criando && (
        <AvisoCreateForm
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

function AvisoCreateForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [titulo, setTitulo] = useState('')
  const [corpo, setCorpo] = useState('')
  const [publicoAlvo, setPublicoAlvo] = useState<PublicoAlvo>('TODOS')
  const [turmaId, setTurmaId] = useState('')
  const [fixado, setFixado] = useState(false)
  const [turmas, setTurmas] = useState<TurmaRead[]>([])
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (publicoAlvo === 'TURMA') {
      turmasApi
        .list({ ativa: true })
        .then(setTurmas)
        .catch(() => {})
    }
  }, [publicoAlvo])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await comunicacaoApi.criarAviso({
        titulo,
        corpo,
        publico_alvo: publicoAlvo,
        turma_id: publicoAlvo === 'TURMA' ? Number(turmaId) : null,
        fixado,
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Novo aviso" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Título</label>
          <input
            required
            maxLength={200}
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            className="input"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Mensagem</label>
          <textarea
            required
            rows={5}
            value={corpo}
            onChange={(e) => setCorpo(e.target.value)}
            className="input"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Público-alvo
            </label>
            <select
              value={publicoAlvo}
              onChange={(e) => setPublicoAlvo(e.target.value as PublicoAlvo)}
              className="input"
            >
              {Object.entries(PUBLICO_ALVO_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          {publicoAlvo === 'TURMA' && (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Turma</label>
              <select
                required
                value={turmaId}
                onChange={(e) => setTurmaId(e.target.value)}
                className="input"
              >
                <option value="">Selecione a turma</option>
                {turmas.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.nome}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={fixado}
            onChange={(e) => setFixado(e.target.checked)}
            className="h-4 w-4 rounded border-slate-300"
          />
          Fixar no topo do mural
        </label>

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
            {salvando ? 'Publicando...' : 'Publicar aviso'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
