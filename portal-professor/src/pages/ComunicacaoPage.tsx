import { useEffect, useState } from 'react'
import { Plus, Pin, Loader2 } from 'lucide-react'
import { comunicacaoApi } from '../api/comunicacao'
import { turmasApi } from '../api/turmas'
import { apiErrorMessage } from '../api/client'
import type { AvisoRead, TurmaRead } from '../types/api'
import { PUBLICO_ALVO_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'

export function ComunicacaoPage() {
  const [avisos, setAvisos] = useState<AvisoRead[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [criando, setCriando] = useState(false)

  function reload() {
    setLoading(true)
    setErro(null)
    comunicacaoApi
      .listarAvisos({ limit: 50 })
      .then((p) => setAvisos(p.items))
      .catch((err) => setErro(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(reload, [])

  async function marcarLido(id: number) {
    try {
      await comunicacaoApi.marcarLido(id)
      setAvisos((prev) => prev.map((a) => (a.id === id ? { ...a, lido: true } : a)))
    } catch {
      /* silencioso */
    }
  }

  return (
    <div>
      <PageHeader
        title="Comunicação"
        subtitle="Mural de avisos"
        action={
          <button
            onClick={() => setCriando(true)}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            <Plus size={16} />
            Novo aviso
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
        <div className="space-y-3">
          {avisos.map((a) => (
            <button
              key={a.id}
              onClick={() => !a.lido && marcarLido(a.id)}
              className="w-full rounded-xl border border-slate-200 bg-white p-4 text-left transition-shadow hover:shadow-sm"
            >
              <div className="mb-1 flex items-center gap-2">
                {a.fixado && <Pin size={14} className="text-amber-500" />}
                <h3 className="font-semibold text-slate-900">{a.titulo}</h3>
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                  {PUBLICO_ALVO_LABELS[a.publico_alvo]}
                </span>
                {!a.lido && (
                  <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                    novo
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-600">{a.corpo}</p>
              <p className="mt-2 text-xs text-slate-400">
                {new Date(a.publicado_em).toLocaleString('pt-BR')}
              </p>
            </button>
          ))}
          {avisos.length === 0 && (
            <p className="py-8 text-center text-slate-400">Nenhum aviso publicado ainda.</p>
          )}
        </div>
      )}

      {criando && (
        <NovoAvisoModal
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

function NovoAvisoModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [turmas, setTurmas] = useState<TurmaRead[]>([])
  const [titulo, setTitulo] = useState('')
  const [corpo, setCorpo] = useState('')
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
      await comunicacaoApi.criarAviso({
        titulo,
        corpo,
        publico_alvo: 'TURMA',
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
    <Modal title="Novo aviso" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
          Professores só publicam avisos para uma turma específica em que lecionam.
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
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Mensagem</label>
          <textarea
            required
            rows={4}
            value={corpo}
            onChange={(e) => setCorpo(e.target.value)}
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
            {salvando ? 'Publicando...' : 'Publicar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
