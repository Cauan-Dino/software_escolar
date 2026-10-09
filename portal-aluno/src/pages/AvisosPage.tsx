import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { alunoApi } from '../api/aluno'
import type { AvisoRead } from '../types/api'

export function AvisosPage() {
  const [avisos, setAvisos] = useState<AvisoRead[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    alunoApi
      .avisos()
      .then((page) => setAvisos(page.items))
      .catch(() => setErro('Não foi possível carregar os avisos.'))
      .finally(() => setLoading(false))
  }, [])

  async function marcarLido(id: number) {
    setAvisos((prev) => prev.map((a) => (a.id === id ? { ...a, lido: true } : a)))
    try {
      await alunoApi.marcarAvisoLido(id)
    } catch {
      setAvisos((prev) => prev.map((a) => (a.id === id ? { ...a, lido: false } : a)))
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400">
        <Loader2 className="animate-spin" />
      </div>
    )
  }

  if (erro) {
    return <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{erro}</p>
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold text-slate-900">Mural de avisos</h1>

      {avisos.length === 0 && <p className="text-sm text-slate-400">Nenhum aviso publicado.</p>}

      <div className="space-y-2">
        {avisos.map((av) => (
          <div
            key={av.id}
            className={`rounded-xl border p-4 ${
              av.lido ? 'border-slate-200 bg-white' : 'border-emerald-200 bg-emerald-50/40'
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-semibold text-slate-900">{av.titulo}</p>
              {!av.lido && (
                <button
                  onClick={() => marcarLido(av.id)}
                  className="shrink-0 rounded-full bg-emerald-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-emerald-700"
                >
                  Marcar como lido
                </button>
              )}
            </div>
            <p className="mt-1 whitespace-pre-wrap text-sm text-slate-600">{av.corpo}</p>
            <p className="mt-2 text-xs text-slate-400">
              {new Date(av.publicado_em).toLocaleDateString('pt-BR')}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
