import { useEffect, useState } from 'react'
import { Plus, Check, X, FileWarning } from 'lucide-react'
import { matriculasApi } from '../api/matriculas'
import { alunosApi } from '../api/pessoas'
import { turmasApi } from '../api/turmas'
import { apiErrorMessage } from '../api/client'
import { useAsyncList } from '../lib/useAsyncList'
import type {
  AlunoListItem,
  MatriculaRead,
  Serie,
  StatusMatricula,
  TurmaRead,
  Turno,
} from '../types/api'
import { SERIE_LABELS, STATUS_MATRICULA_LABELS, TURNO_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'
import { ErrorBanner, ErrorRow, LoadingRow } from '../components/AsyncState'

const STATUS_STYLE: Record<StatusMatricula, string> = {
  PRE_MATRICULA: 'bg-slate-100 text-slate-600',
  EM_ANALISE: 'bg-amber-50 text-amber-700',
  APROVADA: 'bg-emerald-50 text-emerald-700',
  AGUARDANDO_PAGAMENTO: 'bg-sky-50 text-sky-700',
  ATIVA: 'bg-emerald-50 text-emerald-700',
  REJEITADA: 'bg-red-50 text-red-700',
  CANCELADA: 'bg-slate-100 text-slate-500',
}

export function MatriculasPage() {
  const [filtro, setFiltro] = useState<StatusMatricula | 'todas'>('todas')
  const {
    data: matriculas,
    loading,
    error,
    reload,
  } = useAsyncList<MatriculaRead>(
    () =>
      matriculasApi
        .list({ limit: 100, status: filtro === 'todas' ? undefined : filtro })
        .then((p) => p.items),
    [filtro],
  )
  const [criando, setCriando] = useState(false)
  const [aprovando, setAprovando] = useState<MatriculaRead | null>(null)
  const [rejeitando, setRejeitando] = useState<MatriculaRead | null>(null)

  async function iniciarAnaliseSeNecessario(m: MatriculaRead) {
    if (m.status === 'PRE_MATRICULA') {
      await matriculasApi.iniciarAnalise(m.id)
    }
  }

  async function abrirAprovar(m: MatriculaRead) {
    try {
      await iniciarAnaliseSeNecessario(m)
      setAprovando(m)
    } catch (err) {
      alert(apiErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title="Matrículas"
        subtitle={loading ? 'Carregando...' : `${matriculas.length} matrículas registradas`}
        action={
          <button
            onClick={() => setCriando(true)}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            <Plus size={16} />
            Nova matrícula
          </button>
        }
      />

      {error && <ErrorBanner message={error} />}

      <div className="mb-4 flex flex-wrap gap-2">
        {(['todas', ...Object.keys(STATUS_MATRICULA_LABELS)] as (StatusMatricula | 'todas')[]).map(
          (s) => (
            <button
              key={s}
              onClick={() => setFiltro(s)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium ${
                filtro === s
                  ? 'bg-slate-900 text-white'
                  : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50'
              }`}
            >
              {s === 'todas' ? 'Todas' : STATUS_MATRICULA_LABELS[s]}
            </button>
          ),
        )}
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full min-w-[34rem] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-5 py-3 font-medium">Aluno</th>
              <th className="px-5 py-3 font-medium">Série / Turno</th>
              <th className="px-5 py-3 font-medium">Criada em</th>
              <th className="px-5 py-3 font-medium">Documentos</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && <LoadingRow colSpan={6} />}
            {!loading && error && <ErrorRow colSpan={6} message={error} />}
            {!loading &&
              !error &&
              matriculas.map((m) => (
                <tr key={m.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-medium text-slate-900">{m.aluno_nome}</td>
                  <td className="px-5 py-3 text-slate-600">
                    {m.serie_label} · {TURNO_LABELS[m.turno]}
                    {m.turma_nome && (
                      <div className="text-xs text-slate-400">{m.turma_nome}</div>
                    )}
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {new Date(m.created_at).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="px-5 py-3">
                    {m.documentos_pendentes > 0 ? (
                      <span className="flex items-center gap-1 text-amber-600">
                        <FileWarning size={14} />
                        {m.documentos_pendentes} pendente(s)
                      </span>
                    ) : (
                      <span className="text-slate-400">Completo</span>
                    )}
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_STYLE[m.status]}`}
                    >
                      {STATUS_MATRICULA_LABELS[m.status]}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    {(m.status === 'PRE_MATRICULA' || m.status === 'EM_ANALISE') && (
                      <div className="flex justify-end gap-1">
                        <button
                          onClick={() => abrirAprovar(m)}
                          title="Aprovar"
                          className="rounded-md p-1.5 text-slate-400 hover:bg-emerald-50 hover:text-emerald-600"
                        >
                          <Check size={16} />
                        </button>
                        <button
                          onClick={() => setRejeitando(m)}
                          title="Rejeitar"
                          className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            {!loading && !error && matriculas.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                  Nenhuma matrícula encontrada.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {criando && (
        <MatriculaCreateForm
          onClose={() => setCriando(false)}
          onSaved={() => {
            setCriando(false)
            reload()
          }}
        />
      )}
      {aprovando && (
        <AprovarForm
          matricula={aprovando}
          onClose={() => setAprovando(null)}
          onSaved={() => {
            setAprovando(null)
            reload()
          }}
        />
      )}
      {rejeitando && (
        <RejeitarForm
          matricula={rejeitando}
          onClose={() => setRejeitando(null)}
          onSaved={() => {
            setRejeitando(null)
            reload()
          }}
        />
      )}
    </div>
  )
}

function MatriculaCreateForm({
  onClose,
  onSaved,
}: {
  onClose: () => void
  onSaved: () => void
}) {
  const [alunos, setAlunos] = useState<AlunoListItem[]>([])
  const [alunoId, setAlunoId] = useState('')
  const [serie, setSerie] = useState<Serie>('ANO_1')
  const [turno, setTurno] = useState<Turno>('MANHA')
  const [anoLetivo, setAnoLetivo] = useState(new Date().getFullYear())
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    alunosApi
      .list({ limit: 200 })
      .then((p) => setAlunos(p.items))
      .catch(() => {})
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await matriculasApi.create({
        aluno_id: Number(alunoId),
        responsaveis: [],
        ano_letivo: anoLetivo,
        serie,
        turno,
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Nova matrícula" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Aluno
          </label>
          <select
            required
            value={alunoId}
            onChange={(e) => setAlunoId(e.target.value)}
            className="input"
          >
            <option value="">Selecione um aluno já cadastrado</option>
            {alunos.map((a) => (
              <option key={a.id} value={a.id}>
                {a.nome}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-slate-400">
            Cadastre o aluno em "Alunos" antes de criar a matrícula.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Série
            </label>
            <select
              value={serie}
              onChange={(e) => setSerie(e.target.value as Serie)}
              className="input"
            >
              {Object.entries(SERIE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Turno
            </label>
            <select
              value={turno}
              onChange={(e) => setTurno(e.target.value as Turno)}
              className="input"
            >
              {Object.entries(TURNO_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Ano letivo
            </label>
            <input
              type="number"
              required
              value={anoLetivo}
              onChange={(e) => setAnoLetivo(Number(e.target.value))}
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
            {salvando ? 'Salvando...' : 'Criar matrícula'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function AprovarForm({
  matricula,
  onClose,
  onSaved,
}: {
  matricula: MatriculaRead
  onClose: () => void
  onSaved: () => void
}) {
  const [turmas, setTurmas] = useState<TurmaRead[]>([])
  const [turmaId, setTurmaId] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    turmasApi
      .list({ serie: matricula.serie, ano_letivo: matricula.ano_letivo, ativa: true })
      .then(setTurmas)
      .catch(() => {})
  }, [matricula])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await matriculasApi.aprovar(matricula.id, Number(turmaId))
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title={`Aprovar matrícula — ${matricula.aluno_nome}`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Turma ({matricula.serie_label} · {TURNO_LABELS[matricula.turno]})
          </label>
          <select
            required
            value={turmaId}
            onChange={(e) => setTurmaId(e.target.value)}
            className="input"
          >
            <option value="">Selecione a turma</option>
            {turmas.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome} ({t.vagas_disponiveis} vagas)
              </option>
            ))}
          </select>
          {turmas.length === 0 && (
            <p className="mt-1 text-xs text-amber-600">
              Nenhuma turma compatível encontrada para essa série/ano letivo.
            </p>
          )}
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
            {salvando ? 'Aprovando...' : 'Aprovar matrícula'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function RejeitarForm({
  matricula,
  onClose,
  onSaved,
}: {
  matricula: MatriculaRead
  onClose: () => void
  onSaved: () => void
}) {
  const [motivo, setMotivo] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await matriculasApi.rejeitar(matricula.id, motivo)
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title={`Rejeitar matrícula — ${matricula.aluno_nome}`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Motivo da rejeição
          </label>
          <textarea
            required
            minLength={5}
            maxLength={500}
            rows={3}
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            className="input"
          />
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
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60"
          >
            {salvando ? 'Rejeitando...' : 'Rejeitar matrícula'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
