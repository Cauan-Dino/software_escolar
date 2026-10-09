import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { GraduationCap, Users, Loader2 } from 'lucide-react'
import { turmasApi } from '../api/turmas'
import { apiErrorMessage } from '../api/client'
import { TURNO_LABELS, type TurmaRead } from '../types/api'
import { PageHeader } from '../components/PageHeader'

export function MinhasTurmasPage() {
  const [turmas, setTurmas] = useState<TurmaRead[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    turmasApi
      .minhas()
      .then(setTurmas)
      .catch((err) => setErro(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader title="Minhas turmas" subtitle="Turmas em que você leciona" />

      {erro && (
        <p className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{erro}</p>
      )}

      {loading ? (
        <div className="flex justify-center py-16 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {turmas.map((t) => {
            const pct = Math.round((t.vagas_ocupadas / t.capacidade) * 100)
            return (
              <div key={t.id} className="rounded-xl border border-slate-200 bg-white p-5">
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-50 text-sky-600">
                    <GraduationCap size={20} />
                  </div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                    {TURNO_LABELS[t.turno]}
                  </span>
                </div>
                <h3 className="font-semibold text-slate-900">{t.nome}</h3>
                <p className="mb-3 flex items-center gap-1.5 text-xs text-slate-400">
                  <Users size={13} />
                  {t.vagas_ocupadas}/{t.capacidade} alunos ({pct}%)
                </p>

                <div className="flex gap-2">
                  <Link
                    to={`/notas?turma=${t.id}`}
                    className="flex-1 rounded-lg bg-emerald-50 px-3 py-2 text-center text-xs font-medium text-emerald-700 hover:bg-emerald-100"
                  >
                    Lançar notas
                  </Link>
                  <Link
                    to={`/frequencia?turma=${t.id}`}
                    className="flex-1 rounded-lg bg-sky-50 px-3 py-2 text-center text-xs font-medium text-sky-700 hover:bg-sky-100"
                  >
                    Chamada
                  </Link>
                </div>
              </div>
            )
          })}
          {turmas.length === 0 && (
            <p className="col-span-full py-8 text-center text-slate-400">
              Você ainda não está vinculado a nenhuma turma.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
