import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useAuth } from '../lib/AuthContext'
import { alunoApi } from '../api/aluno'
import { PERIODO_LABELS, type BoletimRead } from '../types/api'

const SITUACAO_STYLES: Record<string, string> = {
  APROVADO: 'bg-emerald-50 text-emerald-700',
  RECUPERACAO: 'bg-amber-50 text-amber-700',
  REPROVADO: 'bg-red-50 text-red-700',
  SEM_NOTA: 'bg-slate-100 text-slate-500',
}

const SITUACAO_LABELS: Record<string, string> = {
  APROVADO: 'Aprovado',
  RECUPERACAO: 'Recuperação',
  REPROVADO: 'Reprovado',
  SEM_NOTA: 'Sem nota',
}

export function BoletimPage() {
  const { aluno } = useAuth()
  const [boletim, setBoletim] = useState<BoletimRead | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (!aluno) return
    alunoApi
      .boletim(aluno.id)
      .then(setBoletim)
      .catch(() => setErro('Não foi possível carregar o boletim.'))
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
      <h1 className="text-lg font-semibold text-slate-900">Boletim</h1>

      {boletim?.disciplinas.length === 0 && (
        <p className="text-sm text-slate-400">Nenhuma nota lançada ainda.</p>
      )}

      {boletim?.disciplinas.map((d) => (
        <div key={d.disciplina} className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">{d.disciplina}</h2>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                SITUACAO_STYLES[d.situacao] ?? SITUACAO_STYLES.SEM_NOTA
              }`}
            >
              {SITUACAO_LABELS[d.situacao] ?? d.situacao}
            </span>
          </div>
          <div className="grid grid-cols-4 gap-2 text-center">
            {d.notas.map((n) => (
              <div key={n.periodo} className="rounded-lg bg-slate-50 p-2">
                <p className="text-xs text-slate-400">{PERIODO_LABELS[n.periodo]}</p>
                <p className="text-sm font-semibold text-slate-900">{n.valor.toFixed(1)}</p>
              </div>
            ))}
          </div>
          {d.media !== null && (
            <p className="mt-2 text-right text-xs text-slate-500">
              Média: <span className="font-semibold text-slate-900">{d.media.toFixed(1)}</span>
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
