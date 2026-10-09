import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { frequenciaApi } from '../api/frequencia'
import { apiErrorMessage, isNotFound } from '../api/client'
import { useFilho } from '../lib/FilhoContext'
import type { HistoricoFrequencia } from '../types/api'
import { STATUS_FREQUENCIA_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { SemAcesso } from '../components/SemAcesso'

function hojeISO() {
  return new Date().toISOString().slice(0, 10)
}

function diasAtras(dias: number) {
  const d = new Date()
  d.setDate(d.getDate() - dias)
  return d.toISOString().slice(0, 10)
}

const STATUS_COLOR: Record<string, string> = {
  PRESENTE: 'bg-emerald-50 text-emerald-700',
  FALTA: 'bg-red-50 text-red-700',
  FALTA_JUSTIFICADA: 'bg-amber-50 text-amber-700',
}

export function FrequenciaPage() {
  const { filhoAtivo } = useFilho()
  const [historico, setHistorico] = useState<HistoricoFrequencia | null>(null)
  const [loading, setLoading] = useState(true)
  const [semAcesso, setSemAcesso] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [de] = useState(diasAtras(90))
  const [ate] = useState(hojeISO())

  useEffect(() => {
    if (!filhoAtivo) return
    setLoading(true)
    setErro(null)
    setSemAcesso(false)
    frequenciaApi
      .historico(filhoAtivo.id, de, ate)
      .then(setHistorico)
      .catch((err) => {
        if (isNotFound(err)) setSemAcesso(true)
        else setErro(apiErrorMessage(err))
      })
      .finally(() => setLoading(false))
  }, [filhoAtivo, de, ate])

  if (!filhoAtivo) return <p className="text-slate-500">Selecione um filho.</p>

  return (
    <div>
      <PageHeader title="Frequência" subtitle={`Histórico de ${filhoAtivo.nome} (últimos 90 dias)`} />

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
        <>
          <div className="mb-4 rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm text-slate-500">Percentual de presença no período</p>
            <p className="text-3xl font-semibold text-slate-900">
              {historico?.percentual_presenca.toFixed(1)}%
            </p>
          </div>

          <div className="space-y-2">
            {historico?.registros
              .slice()
              .reverse()
              .map((r) => (
                <div
                  key={r.id}
                  className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {new Date(r.data + 'T00:00').toLocaleDateString('pt-BR')}
                    </p>
                    {r.observacao && <p className="text-xs text-slate-400">{r.observacao}</p>}
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_COLOR[r.status]}`}
                  >
                    {STATUS_FREQUENCIA_LABELS[r.status]}
                  </span>
                </div>
              ))}
            {historico?.registros.length === 0 && (
              <p className="py-8 text-center text-slate-400">Nenhum registro no período.</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}
