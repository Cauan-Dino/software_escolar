import { useState } from 'react'
import { Plus, Search, Pencil, ShieldCheck, ShieldOff } from 'lucide-react'
import { responsaveisApi } from '../api/pessoas'
import { apiErrorMessage } from '../api/client'
import { usePaginatedList } from '../lib/usePaginatedList'
import type { ResponsavelListItem, ResponsavelRead } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'
import { Pagination } from '../components/Pagination'
import { ErrorBanner, ErrorRow, LoadingRow } from '../components/AsyncState'

export function ResponsaveisPage() {
  const [busca, setBusca] = useState('')
  const {
    data: responsaveis,
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
  } = usePaginatedList<ResponsavelListItem>(
    (params) => responsaveisApi.list({ ...params, busca: busca || undefined }),
    [busca],
  )
  const [editando, setEditando] = useState<ResponsavelRead | null>(null)
  const [criando, setCriando] = useState(false)
  const [concedendoAcessoId, setConcedendoAcessoId] = useState<number | null>(null)

  async function abrirEdicao(id: number) {
    const r = await responsaveisApi.get(id)
    setEditando(r)
  }

  return (
    <div>
      <PageHeader
        title="Responsáveis"
        subtitle={loading ? 'Carregando...' : `${total} responsáveis cadastrados`}
        action={
          <button
            onClick={() => setCriando(true)}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            <Plus size={16} />
            Novo responsável
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
              <th className="px-5 py-3 font-medium">CPF</th>
              <th className="px-5 py-3 font-medium">Contato</th>
              <th className="px-5 py-3 font-medium">Acesso ao portal</th>
              <th className="px-5 py-3 font-medium text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && <LoadingRow colSpan={5} />}
            {!loading && error && <ErrorRow colSpan={5} message={error} />}
            {!loading &&
              !error &&
              responsaveis.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-medium text-slate-900">{r.nome}</td>
                  <td className="px-5 py-3 text-slate-600">{r.cpf}</td>
                  <td className="px-5 py-3 text-slate-600">
                    <div>{r.email ?? '—'}</div>
                    <div className="text-xs text-slate-400">{r.telefone ?? ''}</div>
                  </td>
                  <td className="px-5 py-3">
                    {r.tem_acesso ? (
                      <span className="flex w-fit items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                        <ShieldCheck size={14} />
                        Liberado
                      </span>
                    ) : (
                      <button
                        onClick={() => setConcedendoAcessoId(r.id)}
                        className="flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-500 hover:bg-slate-200"
                      >
                        <ShieldOff size={14} />
                        Conceder acesso
                      </button>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => abrirEdicao(r.id)}
                      className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                    >
                      <Pencil size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            {!loading && !error && responsaveis.length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-8 text-center text-slate-400">
                  Nenhum responsável encontrado.
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
        <ResponsavelCreateForm
          onClose={() => setCriando(false)}
          onSaved={() => {
            setCriando(false)
            reload()
          }}
        />
      )}
      {editando && (
        <ResponsavelEditForm
          responsavel={editando}
          onClose={() => setEditando(null)}
          onSaved={() => {
            setEditando(null)
            reload()
          }}
        />
      )}
      {concedendoAcessoId !== null && (
        <ConcederAcessoForm
          responsavelId={concedendoAcessoId}
          onClose={() => setConcedendoAcessoId(null)}
          onSaved={() => {
            setConcedendoAcessoId(null)
            reload()
          }}
        />
      )}
    </div>
  )
}

function ResponsavelCreateForm({
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
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await responsaveisApi.create({
        nome,
        cpf,
        email: email || null,
        telefone: telefone || null,
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Novo responsável" onClose={onClose}>
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

function ResponsavelEditForm({
  responsavel,
  onClose,
  onSaved,
}: {
  responsavel: ResponsavelRead
  onClose: () => void
  onSaved: () => void
}) {
  const [nome, setNome] = useState(responsavel.nome)
  const [email, setEmail] = useState(responsavel.email ?? '')
  const [telefone, setTelefone] = useState(responsavel.telefone ?? '')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await responsaveisApi.update(responsavel.id, {
        nome,
        email: email || null,
        telefone: telefone || null,
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Editar responsável" onClose={onClose}>
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

function ConcederAcessoForm({
  responsavelId,
  onClose,
  onSaved,
}: {
  responsavelId: number
  onClose: () => void
  onSaved: () => void
}) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await responsaveisApi.grantAcesso(responsavelId, email, password)
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Conceder acesso ao portal" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            E-mail de acesso
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Senha provisória
          </label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
          />
          <p className="mt-1 text-xs text-slate-400">
            Mínimo 8 caracteres, com letras e números.
          </p>
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
            {salvando ? 'Salvando...' : 'Conceder acesso'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
