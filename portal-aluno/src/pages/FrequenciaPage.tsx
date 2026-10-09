import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useAuth } from '../lib/AuthContext'
import { alunoApi } from '../api/aluno'
import { STATUS_FREQUENCIA_LABELS, type HistoricoFrequencia } from '../types/api'

function inicioAno(): string {
  return `${new Date().getFullYear()}-01-01`
}

function hoje(): string {
  return new Date().toISOString().slice(0, 10)
}

const STATUS_STYLES: Record<string, string> = {
  PRESENTE: 'bg-emerald-50 text-emerald-700',
  FALTA: 'bg-red-50 text-red-700',
  FALTA_JUSTIFICADA: 'bg-amber-50 text-amber-700',
}

export function FrequenciaPage() {
  const { aluno } = useAuth()
  const [historico, setHistorico] = useState<HistoricoFrequencia | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (!aluno) return
    alunoApi
      .frequencia(aluno.id, inicioAno(), hoje())
      .then(setHistorico)
      .catch(() => setErro('Não foi possível carregar a frequência.'))
      .finally(() => setLoading(false))
  }, [aluno])

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
      <h1 className="text-lg font-semibold text-slate-900">Frequência</h1>

      <div className="rounded-xl border border-slate-200 bg-white p-6 text-center">
        <p className="text-4xl font-bold text-emerald-600">
          {historico?.percentual_presenca.toFixed(0)}%
        </p>
        <p className="text-sm text-slate-500">de presença no ano</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white">
        {historico?.registros.length === 0 && (
          <p className="p-4 text-sm text-slate-400">Nenhum registro no período.</p>
        )}
        {historico?.registros
          .slice()
          .reverse()
          .map((r) => (
            <div
              key={r.id}
              className="flex items-center justify-between border-b border-slate-100 px-4 py-2.5 last:border-0"
            >
              <span className="text-sm text-slate-700">
                {new Date(r.data).toLocaleDateString('pt-BR')}
              </span>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[r.status]}`}
              >
                {STATUS_FREQUENCIA_LABELS[r.status]}
              </span>
            </div>
          ))}
      </div>
    </div>
  )
}
