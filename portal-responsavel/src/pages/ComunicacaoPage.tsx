import { useEffect, useState } from 'react'
import { Pin, Loader2 } from 'lucide-react'
import { comunicacaoApi } from '../api/comunicacao'
import { apiErrorMessage } from '../api/client'
import type { AvisoRead } from '../types/api'
import { PUBLICO_ALVO_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'

export function ComunicacaoPage() {
  const [avisos, setAvisos] = useState<AvisoRead[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

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
      <PageHeader title="Mural de avisos" subtitle="Comunicados da escola" />

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
    </div>
  )
}
