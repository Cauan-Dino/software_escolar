import { useEffect, useState } from 'react'
import { Plus, Search, Pencil, Trash2, Loader2 } from 'lucide-react'
import { alunosApi, responsaveisApi } from '../api/pessoas'
import { apiErrorMessage } from '../api/client'
import { usePaginatedList } from '../lib/usePaginatedList'
import type {
  AlunoListItem,
  AlunoRead,
  Parentesco,
  ResponsavelListItem,
} from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'
import { Pagination } from '../components/Pagination'
import { ErrorBanner, ErrorRow, LoadingRow } from '../components/AsyncState'

const PARENTESCO_LABELS: Record<Parentesco, string> = {
  MAE: 'Mãe',
  PAI: 'Pai',
  AVO: 'Avó/Avô',
  TIO: 'Tio/Tia',
  OUTRO: 'Outro',
}

export function AlunosPage() {
  const [busca, setBusca] = useState('')
  const {
    data: alunos,
    total,
    loading,
    error,
    reload,
    offset,
    pageSize,
    hasPrev,
    hasNext,
    goPrev,
    goNext,
  } = usePaginatedList<AlunoListItem>(
    (params) => alunosApi.list({ ...params, busca: busca || undefined }),
    [busca],
  )
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [criando, setCriando] = useState(false)

  async function remover(id: number) {
    if (!confirm('Remover este aluno?')) return
    try {
      await alunosApi.remove(id)
      reload()
    } catch (err) {
      alert(apiErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title="Alunos"
        subtitle={loading ? 'Carregando...' : `${total} alunos cadastrados`}
        action={
          <button
            onClick={() => setCriando(true)}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            <Plus size={16} />
            Novo aluno
          </button>
        }
      />

      {error && <ErrorBanner message={error} />}

      <div className="mb-4 relative max-w-sm">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
        />
        <input
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar por nome ou CPF..."
          className="w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
        />
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-5 py-3 font-medium">Nome</th>
              <th className="px-5 py-3 font-medium">Data de nascimento</th>
              <th className="px-5 py-3 font-medium">CPF</th>
              <th className="px-5 py-3 font-medium text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && <LoadingRow colSpan={4} />}
            {!loading && error && <ErrorRow colSpan={4} message={error} />}
            {!loading &&
              !error &&
              alunos.map((aluno) => (
                <tr key={aluno.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-medium text-slate-900">
                    {aluno.nome}
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {new Date(aluno.data_nascimento).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {aluno.cpf ?? <span className="text-slate-400">—</span>}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex justify-end gap-1">
                      <button
                        onClick={() => setEditandoId(aluno.id)}
                        className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        onClick={() => remover(aluno.id)}
                        className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            {!loading && !error && alunos.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-slate-400">
                  Nenhum aluno encontrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Pagination
        offset={offset}
        pageSize={pageSize}
        total={total}
        hasPrev={hasPrev}
        hasNext={hasNext}
        onPrev={goPrev}
        onNext={goNext}
      />

      {criando && (
        <AlunoCreateForm
          onClose={() => setCriando(false)}
          onSaved={() => {
            setCriando(false)
            reload()
          }}
        />
      )}
      {editandoId !== null && (
        <AlunoEditModal
          alunoId={editandoId}
          onClose={() => setEditandoId(null)}
          onSaved={() => {
            setEditandoId(null)
            reload()
          }}
        />
      )}
    </div>
  )
}

function AlunoCreateForm({
  onClose,
  onSaved,
}: {
  onClose: () => void
  onSaved: () => void
}) {
  const [nome, setNome] = useState('')
  const [dataNascimento, setDataNascimento] = useState('')
  const [cpf, setCpf] = useState('')
  const [responsavelId, setResponsavelId] = useState('')
  const [parentesco, setParentesco] = useState<Parentesco>('MAE')
  const [responsaveis, setResponsaveis] = useState<ResponsavelListItem[]>([])
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    responsaveisApi
      .list({ limit: 200 })
      .then((p) => setResponsaveis(p.items))
      .catch(() => {})
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await alunosApi.create({
        nome,
        data_nascimento: dataNascimento,
        cpf: cpf || null,
        responsaveis: [
          {
            responsavel_id: Number(responsavelId),
            parentesco,
            responsavel_financeiro: true,
            pode_buscar: true,
          },
        ],
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Novo aluno" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Nome completo
          </label>
          <input
            required
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            className="input"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Data de nascimento
            </label>
            <input
              type="date"
              required
              value={dataNascimento}
              onChange={(e) => setDataNascimento(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              CPF (opcional)
            </label>
            <input
              value={cpf}
              onChange={(e) => setCpf(e.target.value)}
              placeholder="000.000.000-00"
              className="input"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Responsável financeiro
            </label>
            <select
              required
              value={responsavelId}
              onChange={(e) => setResponsavelId(e.target.value)}
              className="input"
            >
              <option value="">Selecione...</option>
              {responsaveis.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.nome}
                </option>
              ))}
            </select>
            {responsaveis.length === 0 && (
              <p className="mt-1 text-xs text-amber-600">
                Nenhum responsável cadastrado ainda — crie um em "Responsáveis" primeiro.
              </p>
            )}
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Parentesco
            </label>
            <select
              value={parentesco}
              onChange={(e) => setParentesco(e.target.value as Parentesco)}
              className="input"
            >
              {Object.entries(PARENTESCO_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {erro && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>
        )}

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

function AlunoEditModal({
  alunoId,
  onClose,
  onSaved,
}: {
  alunoId: number
  onClose: () => void
  onSaved: () => void
}) {
  const [aluno, setAluno] = useState<AlunoRead | null>(null)
  const [nome, setNome] = useState('')
  const [dataNascimento, setDataNascimento] = useState('')
  const [cpf, setCpf] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    alunosApi.get(alunoId).then((a) => {
      setAluno(a)
      setNome(a.nome)
      setDataNascimento(a.data_nascimento)
      setCpf(a.cpf ?? '')
    })
  }, [alunoId])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await alunosApi.update(alunoId, {
        nome,
        data_nascimento: dataNascimento,
        cpf: cpf || null,
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Editar aluno" onClose={onClose}>
      {!aluno ? (
        <div className="flex justify-center py-8 text-slate-400">
          <Loader2 className="animate-spin" size={22} />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Nome completo
            </label>
            <input
              required
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              className="input"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Data de nascimento
              </label>
              <input
                type="date"
                required
                value={dataNascimento}
                onChange={(e) => setDataNascimento(e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                CPF
              </label>
              <input
                value={cpf}
                onChange={(e) => setCpf(e.target.value)}
                className="input"
              />
            </div>
          </div>

          {aluno.responsaveis.length > 0 && (
            <div>
              <p className="mb-1.5 text-sm font-medium text-slate-700">
                Responsáveis vinculados
              </p>
              <div className="space-y-1 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
                {aluno.responsaveis.map((v) => (
                  <div key={v.responsavel_id} className="flex justify-between">
                    <span>
                      {v.nome} ({PARENTESCO_LABELS[v.parentesco]})
                    </span>
                    {v.responsavel_financeiro && (
                      <span className="text-xs font-medium text-emerald-600">
                        Financeiro
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {erro && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>
          )}

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
      )}
    </Modal>
  )
}
