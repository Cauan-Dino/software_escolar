import { useState } from 'react'
import { Plus, Search, Pencil, Trash2 } from 'lucide-react'
import { professoresApi } from '../api/pessoas'
import { apiErrorMessage } from '../api/client'
import { useAsyncList } from '../lib/useAsyncList'
import type { ProfessorListItem } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'
import { ErrorBanner, ErrorRow, LoadingRow } from '../components/AsyncState'

export function ProfessoresPage() {
  const [busca, setBusca] = useState('')
  const {
    data: professores,
    loading,
    error,
    reload,
  } = useAsyncList<ProfessorListItem>(
    () => professoresApi.list({ busca: busca || undefined, limit: 100 }).then((p) => p.items),
    [busca],
  )
  const [editando, setEditando] = useState<ProfessorListItem | null>(null)
  const [criando, setCriando] = useState(false)

  async function remover(id: number) {
    if (!confirm('Remover este professor?')) return
    try {
      await professoresApi.remove(id)
      reload()
    } catch (err) {
      alert(apiErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title="Professores"
        subtitle={loading ? 'Carregando...' : `${professores.length} professores cadastrados`}
        action={
          <button
            onClick={() => setCriando(true)}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            <Plus size={16} />
            Novo professor
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
              <th className="px-5 py-3 font-medium">Formação</th>
              <th className="px-5 py-3 font-medium">CPF</th>
              <th className="px-5 py-3 font-medium">E-mail</th>
              <th className="px-5 py-3 font-medium text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && <LoadingRow colSpan={5} />}
            {!loading && error && <ErrorRow colSpan={5} message={error} />}
            {!loading &&
              !error &&
              professores.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-medium text-slate-900">{p.nome}</td>
                  <td className="px-5 py-3 text-slate-600">
                    {p.formacao ?? <span className="text-slate-400">—</span>}
                  </td>
                  <td className="px-5 py-3 text-slate-600">{p.cpf}</td>
                  <td className="px-5 py-3 text-slate-600">{p.email ?? '—'}</td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex justify-end gap-1">
                      <button
                        onClick={() => setEditando(p)}
                        className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        onClick={() => remover(p.id)}
                        className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            {!loading && !error && professores.length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-8 text-center text-slate-400">
                  Nenhum professor encontrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {criando && (
        <ProfessorCreateForm
          onClose={() => setCriando(false)}
          onSaved={() => {
            setCriando(false)
            reload()
          }}
        />
      )}
      {editando && (
        <ProfessorEditForm
          professor={editando}
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

function ProfessorCreateForm({
  onClose,
  onSaved,
}: {
  onClose: () => void
  onSaved: () => void
}) {
  const [nome, setNome] = useState('')
  const [cpf, setCpf] = useState('')
  const [email, setEmail] = useState('')
  const [telefone, setTelefone] = useState('')
  const [formacao, setFormacao] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await professoresApi.create({
        nome,
        cpf,
        email: email || null,
        telefone: telefone || null,
        formacao: formacao || null,
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Novo professor" onClose={onClose}>
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
              CPF
            </label>
            <input
              required
              value={cpf}
              onChange={(e) => setCpf(e.target.value)}
              placeholder="000.000.000-00"
              className="input"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Formação
            </label>
            <input
              value={formacao}
              onChange={(e) => setFormacao(e.target.value)}
              className="input"
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              E-mail
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Telefone
            </label>
            <input
              value={telefone}
              onChange={(e) => setTelefone(e.target.value)}
              className="input"
            />
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

function ProfessorEditForm({
  professor,
  onClose,
  onSaved,
}: {
  professor: ProfessorListItem
  onClose: () => void
  onSaved: () => void
}) {
  const [nome, setNome] = useState(professor.nome)
  const [email, setEmail] = useState(professor.email ?? '')
  const [formacao, setFormacao] = useState(professor.formacao ?? '')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await professoresApi.update(professor.id, {
        nome,
        email: email || null,
        formacao: formacao || null,
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Editar professor" onClose={onClose}>
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
              E-mail
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Formação
            </label>
            <input
              value={formacao}
              onChange={(e) => setFormacao(e.target.value)}
              className="input"
            />
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
