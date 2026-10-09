import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { notasApi } from '../api/notas'
import { apiErrorMessage, isNotFound } from '../api/client'
import { useFilho } from '../lib/FilhoContext'
import type { BoletimRead } from '../types/api'
import { PERIODO_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { SemAcesso } from '../components/SemAcesso'

export function BoletimPage() {
  const { filhoAtivo } = useFilho()
  const [boletim, setBoletim] = useState<BoletimRead | null>(null)
  const [loading, setLoading] = useState(true)
  const [semAcesso, setSemAcesso] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (!filhoAtivo) return
    setLoading(true)
    setErro(null)
    setSemAcesso(false)
    notasApi
      .boletim(filhoAtivo.id)
      .then(setBoletim)
      .catch((err) => {
        if (isNotFound(err)) setSemAcesso(true)
        else setErro(apiErrorMessage(err))
      })
      .finally(() => setLoading(false))
  }, [filhoAtivo])

  if (!filhoAtivo) return <p className="text-slate-500">Selecione um filho.</p>

  return (
    <div>
      <PageHeader title="Boletim" subtitle={`Notas de ${filhoAtivo.nome}`} />

      {erro && (
        <p className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{erro}</p>
      )}

      {loading ? (
        <div className="flex justify-center py-16 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : semAcesso ? (
        <SemAcesso />
      ) : (
        <div className="space-y-3">
          {boletim?.disciplinas.map((d) => (
            <div key={d.disciplina} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-semibold text-slate-900">{d.disciplina}</h3>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-500">
                    Média: <span className="font-medium text-slate-900">{d.media ?? '-'}</span>
                  </span>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                      d.situacao === 'APROVADO'
                        ? 'bg-emerald-50 text-emerald-700'
                        : d.situacao === 'REPROVADO'
                          ? 'bg-red-50 text-red-700'
                          : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {d.situacao}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-4 gap-2">
                {d.notas.map((n) => (
                  <div
                    key={n.periodo}
                    className="rounded-lg bg-slate-50 px-3 py-2 text-center"
                  >
                    <p className="text-xs text-slate-400">{PERIODO_LABELS[n.periodo]}</p>
                    <p className="text-sm font-semibold text-slate-900">{n.valor}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
          {boletim?.disciplinas.length === 0 && (
            <p className="py-8 text-center text-slate-400">Nenhuma nota lançada ainda.</p>
          )}
        </div>
      )}
    </div>
  )
}
