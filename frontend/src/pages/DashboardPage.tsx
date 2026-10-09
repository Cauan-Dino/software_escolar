import { useEffect, useState } from 'react'
import { Users2, GraduationCap, ClipboardList, AlertCircle, Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { alunosApi } from '../api/pessoas'
import { turmasApi } from '../api/turmas'
import { matriculasApi } from '../api/matriculas'
import { apiErrorMessage } from '../api/client'
import type { MatriculaRead, TurmaRead } from '../types/api'
import { STATUS_MATRICULA_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { ErrorBanner } from '../components/AsyncState'

export function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [totalAlunos, setTotalAlunos] = useState(0)
  const [turmas, setTurmas] = useState<TurmaRead[]>([])
  const [recentes, setRecentes] = useState<MatriculaRead[]>([])
  const [emAnalise, setEmAnalise] = useState(0)
  const [documentosPendentes, setDocumentosPendentes] = useState(0)

  useEffect(() => {
    Promise.all([
      alunosApi.list({ limit: 1 }),
      turmasApi.list({ ativa: true }),
      matriculasApi.list({ limit: 5 }),
      matriculasApi.list({ limit: 1, status: 'EM_ANALISE' }),
      matriculasApi.list({ limit: 1, status: 'PRE_MATRICULA' }),
      matriculasApi.list({ limit: 200, status: 'EM_ANALISE' }),
    ])
      .then(([alunosPage, turmasList, matriculasPage, emAnalisePage, preMatriculaPage, emAnaliseDetalhado]) => {
        setTotalAlunos(alunosPage.total)
        setTurmas(turmasList)
        setRecentes(matriculasPage.items)
        setEmAnalise(emAnalisePage.total + preMatriculaPage.total)
        setDocumentosPendentes(
          emAnaliseDetalhado.items.reduce((acc, m) => acc + m.documentos_pendentes, 0),
        )
      })
      .catch((err) => setErro(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  const stats = [
    { label: 'Alunos cadastrados', value: totalAlunos, icon: Users2, color: 'bg-emerald-100 text-emerald-700', bar: 'from-emerald-400' },
    { label: 'Turmas ativas', value: turmas.length, icon: GraduationCap, color: 'bg-sky-100 text-sky-700', bar: 'from-sky-400' },
    { label: 'Matrículas em análise', value: emAnalise, icon: ClipboardList, color: 'bg-amber-100 text-amber-700', bar: 'from-amber-400' },
    { label: 'Pendências de documentos', value: documentosPendentes, icon: AlertCircle, color: 'bg-red-100 text-red-700', bar: 'from-red-400' },
  ]

  if (loading) {
    return (
      <div className="flex justify-center py-20 text-slate-400">
        <Loader2 className="animate-spin" size={24} />
      </div>
    )
  }

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Visão geral do Semeando" />

      {erro && <ErrorBanner message={erro} />}

      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon, color, bar }) => (
          <div
            key={label}
            className="card relative overflow-hidden p-5 transition-shadow hover:shadow-lift"
          >
            <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${bar} to-transparent`} />
            <div className="flex items-start justify-between">
              <p className="font-display text-4xl font-semibold tracking-tight text-slate-900">
                {value}
              </p>
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${color}`}>
                <Icon size={19} />
              </div>
            </div>
            <p className="mt-3 text-sm text-slate-500">{label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Matrículas recentes</h2>
            <Link to="/matriculas" className="text-sm font-medium text-emerald-700 hover:text-emerald-800">
              Ver todas
            </Link>
          </div>
          <div className="space-y-1">
            {recentes.map((m) => (
              <div
                key={m.id}
                className="-mx-2 flex items-center justify-between gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-slate-50"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-800">
                    {m.aluno_nome.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">{m.aluno_nome}</p>
                    <p className="truncate text-xs text-slate-500">{m.serie_label}</p>
                  </div>
                </div>
                <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                  {STATUS_MATRICULA_LABELS[m.status]}
                </span>
              </div>
            ))}
            {recentes.length === 0 && (
              <p className="py-4 text-center text-sm text-slate-400">
                Nenhuma matrícula ainda.
              </p>
            )}
          </div>
        </div>

        <div className="card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Ocupação das turmas</h2>
            <Link to="/turmas" className="text-sm font-medium text-emerald-700 hover:text-emerald-800">
              Ver todas
            </Link>
          </div>
          <div className="space-y-5">
            {turmas.map((t) => {
              const pct = Math.round((t.vagas_ocupadas / t.capacidade) * 100)
              return (
                <div key={t.id}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-700">{t.nome}</span>
                    <span className="text-slate-500">
                      {t.vagas_ocupadas}/{t.capacidade}
                    </span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className={`h-full rounded-full ${pct >= 100 ? 'bg-red-500' : 'bg-gradient-to-r from-emerald-400 to-emerald-600'}`}
                      style={{ width: `${Math.min(pct, 100)}%` }}
                    />
                  </div>
                </div>
              )
            })}
            {turmas.length === 0 && (
              <p className="py-4 text-center text-sm text-slate-400">
                Nenhuma turma ativa.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
