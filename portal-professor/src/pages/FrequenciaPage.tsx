import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Loader2, CheckCircle2 } from 'lucide-react'
import { turmasApi } from '../api/turmas'
import { frequenciaApi } from '../api/frequencia'
import { apiErrorMessage } from '../api/client'
import type { AlunoChamada, StatusFrequencia, TurmaRead } from '../types/api'
import { STATUS_FREQUENCIA_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'

const STATUS_COLOR: Record<StatusFrequencia, string> = {
  PRESENTE: 'bg-emerald-600 text-white',
  FALTA: 'bg-red-600 text-white',
  FALTA_JUSTIFICADA: 'bg-amber-500 text-white',
}
const STATUS_COLOR_OFF: Record<StatusFrequencia, string> = {
  PRESENTE: 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100',
  FALTA: 'bg-red-50 text-red-700 hover:bg-red-100',
  FALTA_JUSTIFICADA: 'bg-amber-50 text-amber-700 hover:bg-amber-100',
}

function hoje() {
  return new Date().toISOString().slice(0, 10)
}

export function FrequenciaPage() {
  const [params, setParams] = useSearchParams()
  const [turmas, setTurmas] = useState<TurmaRead[]>([])
  const turmaId = params.get('turma') ? Number(params.get('turma')) : null
  const [data, setData] = useState(hoje())

  useEffect(() => {
    turmasApi.minhas().then(setTurmas)
  }, [])

  return (
    <div>
      <PageHeader title="Frequência" subtitle="Chamada do dia por turma" />

      <div className="mb-6 grid grid-cols-2 gap-4 sm:max-w-md">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Turma</label>
          <select
            value={turmaId ?? ''}
            onChange={(e) => setParams({ turma: e.target.value })}
            className="input"
          >
            <option value="">Selecione...</option>
            {turmas.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Data</label>
          <input
            type="date"
            value={data}
            onChange={(e) => setData(e.target.value)}
            className="input"
          />
        </div>
      </div>

      {turmaId && <Chamada turmaId={turmaId} data={data} />}
      {!turmaId && (
        <p className="py-8 text-center text-sm text-slate-400">
          Selecione uma turma para fazer a chamada.
        </p>
      )}
    </div>
  )
}

function Chamada({ turmaId, data }: { turmaId: number; data: string }) {
  const [alunos, setAlunos] = useState<AlunoChamada[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [salvando, setSalvando] = useState(false)
  const [sucesso, setSucesso] = useState(false)

  useEffect(() => {
    setLoading(true)
    setErro(null)
    setSucesso(false)
    frequenciaApi
      .chamadaDoDia(turmaId, data)
      .then(setAlunos)
      .catch((err) => setErro(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [turmaId, data])

  function setStatus(alunoId: number, status: StatusFrequencia) {
    setAlunos((prev) => prev.map((a) => (a.aluno_id === alunoId ? { ...a, status } : a)))
  }

  async function salvar() {
    setSalvando(true)
    setErro(null)
    setSucesso(false)
    try {
      await frequenciaApi.lancarChamada(
        turmaId,
        data,
        alunos.map((a) => ({ aluno_id: a.aluno_id, status: a.status })),
      )
      setSucesso(true)
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-16 text-slate-400">
        <Loader2 className="animate-spin" size={24} />
      </div>
    )
  }
  if (erro) return <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{erro}</p>

  return (
    <div>
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-5 py-3 font-medium">Aluno</th>
              <th className="px-5 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {alunos.map((a) => (
              <tr key={a.aluno_id} className="hover:bg-slate-50">
                <td className="px-5 py-3 font-medium text-slate-900">{a.aluno_nome}</td>
                <td className="px-5 py-3">
                  <div className="flex gap-2">
                    {(Object.keys(STATUS_FREQUENCIA_LABELS) as StatusFrequencia[]).map((s) => (
                      <button
                        key={s}
                        onClick={() => setStatus(a.aluno_id, s)}
                        className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                          a.status === s ? STATUS_COLOR[s] : STATUS_COLOR_OFF[s]
                        }`}
                      >
                        {STATUS_FREQUENCIA_LABELS[s]}
                      </button>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
            {alunos.length === 0 && (
              <tr>
                <td colSpan={2} className="px-5 py-8 text-center text-slate-400">
                  Nenhum aluno matriculado nesta turma.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {alunos.length > 0 && (
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={salvar}
            disabled={salvando}
            className="rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {salvando ? 'Salvando...' : 'Salvar chamada'}
          </button>
          {sucesso && (
            <span className="flex items-center gap-1.5 text-sm text-emerald-600">
              <CheckCircle2 size={16} />
              Chamada salva.
            </span>
          )}
        </div>
      )}
    </div>
  )
}
