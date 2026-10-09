import { useEffect, useState } from 'react'
import { Check, Loader2, Save, AlertCircle } from 'lucide-react'
import { frequenciaApi } from '../api/frequencia'
import { turmasApi } from '../api/turmas'
import { apiErrorMessage } from '../api/client'
import { useAsyncList } from '../lib/useAsyncList'
import type { TurmaRead } from '../types/api'
import type { AlunoChamada, RegistroFrequenciaInput, StatusFrequencia } from '../types/frequencia'
import { STATUS_FREQUENCIA_LABELS } from '../types/frequencia'
import { PageHeader } from '../components/PageHeader'
import { ErrorBanner } from '../components/AsyncState'

function hoje(): string {
  return new Date().toISOString().slice(0, 10)
}

const STATUS_OPCOES: StatusFrequencia[] = ['PRESENTE', 'FALTA', 'FALTA_JUSTIFICADA']

const STATUS_BUTTON_STYLE: Record<StatusFrequencia, { ativo: string; inativo: string }> = {
  PRESENTE: {
    ativo: 'bg-emerald-600 text-white',
    inativo: 'bg-white text-emerald-700 ring-1 ring-emerald-200 hover:bg-emerald-50',
  },
  FALTA: {
    ativo: 'bg-red-600 text-white',
    inativo: 'bg-white text-red-700 ring-1 ring-red-200 hover:bg-red-50',
  },
  FALTA_JUSTIFICADA: {
    ativo: 'bg-amber-500 text-white',
    inativo: 'bg-white text-amber-700 ring-1 ring-amber-200 hover:bg-amber-50',
  },
}

export function FrequenciaPage() {
  const { data: turmas, loading: carregandoTurmas } = useAsyncList(() => turmasApi.list())
  const [turmaId, setTurmaId] = useState<string>('')
  const [data, setData] = useState<string>(hoje())

  const [alunos, setAlunos] = useState<AlunoChamada[]>([])
  const [carregandoChamada, setCarregandoChamada] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [salvando, setSalvando] = useState(false)
  const [sucesso, setSucesso] = useState(false)

  useEffect(() => {
    if (turmas.length > 0 && !turmaId) {
      setTurmaId(String(turmas[0].id))
    }
  }, [turmas, turmaId])

  useEffect(() => {
    if (!turmaId || !data) {
      setAlunos([])
      return
    }
    setCarregandoChamada(true)
    setErro(null)
    setSucesso(false)
    frequenciaApi
      .listarChamadaDoDia(Number(turmaId), data)
      .then(setAlunos)
      .catch((err) => setErro(apiErrorMessage(err)))
      .finally(() => setCarregandoChamada(false))
  }, [turmaId, data])

  function atualizarStatus(alunoId: number, status: StatusFrequencia) {
    setAlunos((prev) => prev.map((a) => (a.aluno_id === alunoId ? { ...a, status } : a)))
  }

  function atualizarObservacao(alunoId: number, observacao: string) {
    setAlunos((prev) =>
      prev.map((a) => (a.aluno_id === alunoId ? { ...a, observacao: observacao || null } : a)),
    )
  }

  async function salvarChamada() {
    setSalvando(true)
    setErro(null)
    setSucesso(false)
    const registros: RegistroFrequenciaInput[] = alunos.map((a) => ({
      aluno_id: a.aluno_id,
      status: a.status,
      observacao: a.observacao,
    }))
    try {
      await frequenciaApi.lancarChamada(Number(turmaId), data, registros)
      setSucesso(true)
      const atualizados = await frequenciaApi.listarChamadaDoDia(Number(turmaId), data)
      setAlunos(atualizados)
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Frequência"
        subtitle="Lance a chamada do dia por turma"
        action={
          <button
            onClick={salvarChamada}
            disabled={salvando || carregandoChamada || alunos.length === 0}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {salvando ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
            Salvar chamada
          </button>
        }
      />

      <div className="mb-4 flex flex-wrap items-end gap-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Turma</label>
          <select
            value={turmaId}
            onChange={(e) => setTurmaId(e.target.value)}
            className="input"
            disabled={carregandoTurmas}
          >
            {turmas.map((t: TurmaRead) => (
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

      {erro && <ErrorBanner message={erro} />}
      {sucesso && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          <Check size={16} />
          Chamada salva com sucesso.
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full min-w-[34rem] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-5 py-3 font-medium">Aluno</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Observação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {carregandoChamada && (
              <tr>
                <td colSpan={3} className="px-5 py-10 text-center text-slate-400">
                  <Loader2 className="mx-auto mb-2 animate-spin" size={20} />
                  Carregando...
                </td>
              </tr>
            )}
            {!carregandoChamada &&
              alunos.map((a) => (
                <tr key={a.aluno_id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-medium text-slate-900">
                    {a.aluno_nome}
                    {!a.lancado && (
                      <span className="ml-2 inline-flex items-center gap-1 text-xs text-slate-400">
                        <AlertCircle size={12} />
                        não lançado
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex gap-1.5">
                      {STATUS_OPCOES.map((status) => {
                        const ativo = a.status === status
                        const style = STATUS_BUTTON_STYLE[status]
                        return (
                          <button
                            key={status}
                            type="button"
                            onClick={() => atualizarStatus(a.aluno_id, status)}
                            className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                              ativo ? style.ativo : style.inativo
                            }`}
                          >
                            {STATUS_FREQUENCIA_LABELS[status]}
                          </button>
                        )
                      })}
                    </div>
                  </td>
                  <td className="px-5 py-3">
                    <input
                      type="text"
                      value={a.observacao ?? ''}
                      onChange={(e) => atualizarObservacao(a.aluno_id, e.target.value)}
                      placeholder="Opcional"
                      maxLength={500}
                      className="input"
                    />
                  </td>
                </tr>
              ))}
            {!carregandoChamada && alunos.length === 0 && (
              <tr>
                <td colSpan={3} className="px-5 py-8 text-center text-slate-400">
                  {turmaId
                    ? 'Nenhum aluno matriculado (ativo) nesta turma.'
                    : 'Selecione uma turma.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

