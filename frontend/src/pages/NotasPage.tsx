import { useEffect, useMemo, useState } from 'react'
import { BookOpen, ClipboardList, Loader2, Search } from 'lucide-react'
import { notasApi } from '../api/notas'
import { turmasApi } from '../api/turmas'
import { apiErrorMessage } from '../api/client'
import { useAsyncList } from '../lib/useAsyncList'
import { ErrorBanner } from '../components/AsyncState'
import { Modal } from '../components/Modal'
import { PageHeader } from '../components/PageHeader'
import type { BoletimRead, GradeCelula, Periodo } from '../types/notas'
import { PERIODO_LABELS, PERIODOS, SITUACAO_LABELS } from '../types/notas'

type Visao = 'LANCAMENTO' | 'BOLETIM'

export function NotasPage() {
  const [visao, setVisao] = useState<Visao>('LANCAMENTO')

  return (
    <div>
      <PageHeader
        title="Notas"
        subtitle="Lançamento de notas por turma e consulta de boletim por aluno"
        action={
          <div className="flex gap-1 rounded-lg bg-slate-100 p-1">
            <button
              onClick={() => setVisao('LANCAMENTO')}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                visao === 'LANCAMENTO'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <ClipboardList size={15} />
              Lançamento
            </button>
            <button
              onClick={() => setVisao('BOLETIM')}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                visao === 'BOLETIM'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <BookOpen size={15} />
              Boletim
            </button>
          </div>
        }
      />

      {visao === 'LANCAMENTO' ? <LancamentoView /> : <BoletimView />}
    </div>
  )
}

// --- Lançamento: grade da turma por período -------------------------------------------

function LancamentoView() {
  const { data: turmas, loading: turmasLoading, error: turmasError } = useAsyncList(() =>
    turmasApi.list(),
  )
  const [turmaId, setTurmaId] = useState<number | null>(null)
  const [periodo, setPeriodo] = useState<Periodo>('BIMESTRE_1')

  useEffect(() => {
    if (turmaId === null && turmas.length > 0) {
      setTurmaId(turmas[0].id)
    }
  }, [turmas, turmaId])

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-end gap-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Turma</label>
          <select
            className="input"
            value={turmaId ?? ''}
            onChange={(e) => setTurmaId(Number(e.target.value))}
            disabled={turmasLoading}
          >
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
            className="input"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value as Periodo)}
          >
            {PERIODOS.map((p) => (
              <option key={p} value={p}>
                {PERIODO_LABELS[p]}
              </option>
            ))}
          </select>
        </div>
      </div>

      {turmasError && <ErrorBanner message={turmasError} />}

      {turmaId !== null && <GradeTable turmaId={turmaId} periodo={periodo} />}
    </div>
  )
}

function GradeTable({ turmaId, periodo }: { turmaId: number; periodo: Periodo }) {
  const { data, loading, error, reload } = useAsyncListOne(
    () => notasApi.listarGrade(turmaId, periodo),
    [turmaId, periodo],
  )
  const [editando, setEditando] = useState<GradeCelula | null>(null)
  const alunos = useMemoAlunos(data?.celulas ?? [])

  if (loading) {
    return (
      <div className="flex justify-center py-16 text-slate-400">
        <Loader2 className="animate-spin" size={24} />
      </div>
    )
  }
  if (error) return <ErrorBanner message={error} />
  if (!data) return null

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full min-w-[30rem] text-sm">
        <thead>
          <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
            <th className="px-4 py-3">Aluno</th>
            {data.disciplinas.map((d) => (
              <th key={d} className="px-4 py-3">
                {d}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {alunos.map((alunoId) => {
            const nome = data.celulas.find((c) => c.aluno_id === alunoId)?.aluno_nome ?? ''
            return (
              <tr key={alunoId} className="border-b border-slate-50">
                <td className="px-4 py-2.5 font-medium text-slate-800">{nome}</td>
                {data.disciplinas.map((disciplina) => {
                  const celula = data.celulas.find(
                    (c) => c.aluno_id === alunoId && c.disciplina === disciplina,
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
            )
          })}
          {alunos.length === 0 && (
            <tr>
              <td
                colSpan={data.disciplinas.length + 1}
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
  const [valor, setValor] = useState<string>(celula.valor != null ? String(celula.valor) : '')
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
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Nota (0 a 10)
          </label>
          <input
            type="text"
            inputMode="decimal"
            required
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            className="input"
            placeholder="Ex.: 8.5"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Observação (opcional)
          </label>
          <input
            type="text"
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

// --- Boletim: consulta por aluno -------------------------------------------------------

function BoletimView() {
  const [alunoIdInput, setAlunoIdInput] = useState('')
  const [alunoId, setAlunoId] = useState<number | null>(null)
  const [boletim, setBoletim] = useState<BoletimRead | null>(null)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function buscar(e: React.FormEvent) {
    e.preventDefault()
    const id = Number(alunoIdInput)
    if (!id) return
    setAlunoId(id)
    setLoading(true)
    setErro(null)
    setBoletim(null)
    try {
      const data = await notasApi.buscarBoletim(id)
      setBoletim(data)
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <form onSubmit={buscar} className="mb-5 flex items-end gap-3">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            ID do aluno
          </label>
          <input
            type="number"
            className="input w-40"
            value={alunoIdInput}
            onChange={(e) => setAlunoIdInput(e.target.value)}
            placeholder="Ex.: 12"
          />
        </div>
        <button
          type="submit"
          className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
        >
          <Search size={16} />
          Buscar
        </button>
      </form>

      {loading && (
        <div className="flex justify-center py-16 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      )}
      {erro && <ErrorBanner message={erro} />}

      {boletim && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full min-w-[30rem] text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
                <th className="px-4 py-3">Disciplina</th>
                {PERIODOS.map((p) => (
                  <th key={p} className="px-4 py-3">
                    {PERIODO_LABELS[p]}
                  </th>
                ))}
                <th className="px-4 py-3">Média</th>
                <th className="px-4 py-3">Situação</th>
              </tr>
            </thead>
            <tbody>
              {boletim.disciplinas.map((d) => (
                <tr key={d.disciplina} className="border-b border-slate-50">
                  <td className="px-4 py-2.5 font-medium text-slate-800">{d.disciplina}</td>
                  {PERIODOS.map((p) => {
                    const nota = d.notas.find((n) => n.periodo === p)
                    return (
                      <td key={p} className="px-4 py-2.5 text-slate-600">
                        {nota ? nota.valor.toFixed(1) : '—'}
                      </td>
                    )
                  })}
                  <td className="px-4 py-2.5 font-semibold text-slate-800">
                    {d.media != null ? d.media.toFixed(1) : '—'}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-medium ${situacaoClasses(
                        d.situacao,
                      )}`}
                    >
                      {SITUACAO_LABELS[d.situacao]}
                    </span>
                  </td>
                </tr>
              ))}
              {boletim.disciplinas.length === 0 && (
                <tr>
                  <td colSpan={PERIODOS.length + 3} className="px-4 py-10 text-center text-slate-400">
                    Nenhuma nota lançada para este aluno ainda.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {!loading && !erro && !boletim && alunoId !== null && (
        <p className="py-8 text-center text-slate-400">Nenhum resultado.</p>
      )}
    </div>
  )
}

function situacaoClasses(situacao: string): string {
  switch (situacao) {
    case 'APROVADO':
      return 'bg-emerald-50 text-emerald-700'
    case 'RECUPERACAO':
      return 'bg-amber-50 text-amber-700'
    case 'REPROVADO':
      return 'bg-red-50 text-red-700'
    default:
      return 'bg-slate-100 text-slate-500'
  }
}

// --- Helpers locais ---------------------------------------------------------------------

function useMemoAlunos(celulas: GradeCelula[]): number[] {
  return useMemo(() => {
    const seen = new Set<number>()
    const ordered: number[] = []
    for (const c of celulas) {
      if (!seen.has(c.aluno_id)) {
        seen.add(c.aluno_id)
        ordered.push(c.aluno_id)
      }
    }
    return ordered
  }, [celulas])
}

/** Como useAsyncList é tipado para listas, usamos uma variante simples para um objeto só. */
function useAsyncListOne<T>(fetcher: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function reload() {
    setLoading(true)
    setError(null)
    fetcher()
      .then(setData)
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    reload()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading, error, reload }
}
