import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { turmasApi } from '../api/turmas'
import { notasApi } from '../api/notas'
import { apiErrorMessage } from '../api/client'
import { PERIODO_LABELS, type GradeCelula, type Periodo, type TurmaGradeRead, type TurmaRead } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'

export function NotasPage() {
  const [params, setParams] = useSearchParams()
  const [turmas, setTurmas] = useState<TurmaRead[]>([])
  const turmaId = params.get('turma') ? Number(params.get('turma')) : null
  const [periodo, setPeriodo] = useState<Periodo>('BIMESTRE_1')

  useEffect(() => {
    turmasApi.minhas().then(setTurmas)
  }, [])

  return (
    <div>
      <PageHeader title="Notas" subtitle="Lançamento de notas por turma e período" />

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
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Período</label>
          <select
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value as Periodo)}
            className="input"
          >
            {Object.entries(PERIODO_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {turmaId && <GradeTable turmaId={turmaId} periodo={periodo} />}
      {!turmaId && (
        <p className="py-8 text-center text-sm text-slate-400">
          Selecione uma turma para lançar notas.
        </p>
      )}
    </div>
  )
}

function GradeTable({ turmaId, periodo }: { turmaId: number; periodo: Periodo }) {
  const [grade, setGrade] = useState<TurmaGradeRead | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [editando, setEditando] = useState<GradeCelula | null>(null)

  function reload() {
    setLoading(true)
    setErro(null)
    notasApi
      .listarGrade(turmaId, periodo)
      .then(setGrade)
      .catch((err) => setErro(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(reload, [turmaId, periodo])

  const alunos = useMemo(() => {
    const seen = new Set<number>()
    const ordered: { id: number; nome: string }[] = []
    for (const c of grade?.celulas ?? []) {
      if (!seen.has(c.aluno_id)) {
        seen.add(c.aluno_id)
        ordered.push({ id: c.aluno_id, nome: c.aluno_nome })
      }
    }
    return ordered
  }, [grade])

  if (loading) {
    return (
      <div className="flex justify-center py-16 text-slate-400">
        <Loader2 className="animate-spin" size={24} />
      </div>
    )
  }
  if (erro) return <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{erro}</p>
  if (!grade) return null

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
            <th className="px-4 py-3">Aluno</th>
            {grade.disciplinas.map((d) => (
              <th key={d} className="px-4 py-3">
                {d}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {alunos.map((aluno) => (
            <tr key={aluno.id} className="border-b border-slate-50">
              <td className="px-4 py-2.5 font-medium text-slate-800">{aluno.nome}</td>
              {grade.disciplinas.map((disciplina) => {
                const celula = grade.celulas.find(
                  (c) => c.aluno_id === aluno.id && c.disciplina === disciplina,
                )
                return (
                  <td key={disciplina} className="px-4 py-2.5">
                    <button
                      onClick={() => celula && setEditando(celula)}
                      className={`min-w-[3rem] rounded-md px-2 py-1 text-sm ${
                        celula?.valor != null
                          ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                          : 'text-slate-400 hover:bg-slate-100'
                      }`}
                    >
                      {celula?.valor != null ? celula.valor.toFixed(1) : '—'}
                    </button>
                  </td>
                )
              })}
            </tr>
          ))}
          {alunos.length === 0 && (
            <tr>
              <td
                colSpan={grade.disciplinas.length + 1}
                className="px-4 py-10 text-center text-slate-400"
              >
                Nenhum aluno matriculado nesta turma.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {editando && (
        <LancarNotaModal
          turmaId={turmaId}
          celula={editando}
          onClose={() => setEditando(null)}
          onSaved={() => {
            setEditando(null)
            reload()
          }}
        />
      )}
    </div>
  )
}

function LancarNotaModal({
  turmaId,
  celula,
  onClose,
  onSaved,
}: {
  turmaId: number
  celula: GradeCelula
  onClose: () => void
  onSaved: () => void
}) {
  const [valor, setValor] = useState(celula.valor != null ? String(celula.valor) : '')
  const [observacao, setObservacao] = useState(celula.observacao ?? '')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const numero = Number(valor.replace(',', '.'))
    if (Number.isNaN(numero) || numero < 0 || numero > 10) {
      setErro('Informe uma nota entre 0 e 10.')
      return
    }
    setSalvando(true)
    setErro(null)
    try {
      await notasApi.lancarNota(turmaId, celula.aluno_id, {
        disciplina: celula.disciplina,
        periodo: celula.periodo,
        valor: numero,
        observacao: observacao || null,
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title={`${celula.aluno_nome} · ${celula.disciplina}`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Nota (0 a 10)</label>
          <input
            type="text"
            inputMode="decimal"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            placeholder="Ex.: 8.5"
            className="input"
            autoFocus
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Observação (opcional)
          </label>
          <input
            value={observacao}
            onChange={(e) => setObservacao(e.target.value)}
            className="input"
          />
        </div>

        {erro && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={salvando}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {salvando ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
