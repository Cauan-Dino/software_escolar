import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { financeiroApi } from '../api/financeiro'
import { apiErrorMessage, isNotFound } from '../api/client'
import { useFilho } from '../lib/FilhoContext'
import type { CobrancaRead } from '../types/api'
import { STATUS_COBRANCA_LABELS, TIPO_COBRANCA_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { SemAcesso } from '../components/SemAcesso'

const STATUS_COLOR: Record<string, string> = {
  PENDENTE: 'bg-slate-100 text-slate-600',
  PAGA: 'bg-emerald-50 text-emerald-700',
  ATRASADA: 'bg-red-50 text-red-700',
  CANCELADA: 'bg-slate-100 text-slate-400',
}

function formatarMoeda(valor: string) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function FinanceiroPage() {
  const { filhoAtivo } = useFilho()
  const [cobrancas, setCobrancas] = useState<CobrancaRead[]>([])
  const [loading, setLoading] = useState(true)
  const [semAcesso, setSemAcesso] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (!filhoAtivo) return
    setLoading(true)
    setErro(null)
    setSemAcesso(false)
    financeiroApi
      .cobrancas(filhoAtivo.id)
      .then((p) => setCobrancas(p.items))
      .catch((err) => {
        if (isNotFound(err)) setSemAcesso(true)
        else setErro(apiErrorMessage(err))
      })
      .finally(() => setLoading(false))
  }, [filhoAtivo])

  if (!filhoAtivo) return <p className="text-slate-500">Selecione um filho.</p>

  return (
    <div>
      <PageHeader title="Financeiro" subtitle={`Cobranças de ${filhoAtivo.nome} (somente leitura)`} />

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
        <div className="space-y-2">
          {cobrancas.map((c) => (
            <div
              key={c.id}
              className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4"
            >
              <div>
                <p className="text-sm font-medium text-slate-900">
                  {TIPO_COBRANCA_LABELS[c.tipo]}
                  {c.competencia ? ` · ${c.competencia}` : ''}
                </p>
                <p className="text-xs text-slate-400">
                  Vencimento: {new Date(c.vencimento + 'T00:00').toLocaleDateString('pt-BR')}
                </p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-slate-900">{formatarMoeda(c.valor_final)}</p>
                <span
                  className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLOR[c.status]}`}
                >
                  {STATUS_COBRANCA_LABELS[c.status]}
                </span>
              </div>
            </div>
          ))}
          {cobrancas.length === 0 && (
            <p className="py-8 text-center text-slate-400">Nenhuma cobrança registrada.</p>
          )}
        </div>
      )}
    </div>
  )
}
