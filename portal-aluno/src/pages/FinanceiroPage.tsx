import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useAuth } from '../lib/AuthContext'
import { alunoApi } from '../api/aluno'
import { STATUS_COBRANCA_LABELS, type CobrancaRead } from '../types/api'

const STATUS_STYLES: Record<string, string> = {
  PENDENTE: 'bg-amber-50 text-amber-700',
  PAGA: 'bg-emerald-50 text-emerald-700',
  ATRASADA: 'bg-red-50 text-red-700',
  CANCELADA: 'bg-slate-100 text-slate-500',
}

function formatMoeda(valor: string): string {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function FinanceiroPage() {
  const { aluno } = useAuth()
  const [cobrancas, setCobrancas] = useState<CobrancaRead[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (!aluno) return
    alunoApi
      .cobrancas(aluno.id)
      .then((page) => setCobrancas(page.items))
      .catch(() => setErro('Não foi possível carregar as cobranças.'))
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
      <h1 className="text-lg font-semibold text-slate-900">Financeiro</h1>

      {cobrancas.length === 0 && (
        <p className="text-sm text-slate-400">Nenhuma cobrança encontrada.</p>
      )}

      <div className="space-y-2">
        {cobrancas.map((c) => (
          <div key={c.id} className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-900">
                {c.tipo} {c.competencia ? `· ${c.competencia}` : ''}
              </p>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[c.status]}`}
              >
                {STATUS_COBRANCA_LABELS[c.status]}
              </span>
            </div>
            <div className="mt-2 flex items-center justify-between text-sm">
              <span className="text-slate-500">
                Vencimento: {new Date(c.vencimento).toLocaleDateString('pt-BR')}
              </span>
              <span className="font-semibold text-slate-900">{formatMoeda(c.valor_final)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
