import { useEffect, useState, type FormEvent } from 'react'
import { Loader2, Plus, Upload, XCircle } from 'lucide-react'
import { matriculasApi } from '../api/matriculas'
import { apiErrorMessage } from '../api/client'
import { useFilho } from '../lib/FilhoContext'
import type { MatriculaRead, Serie, Turno } from '../types/api'
import { SERIE_LABELS, STATUS_MATRICULA_LABELS, TURNO_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'

const STATUS_COLOR: Record<string, string> = {
  PRE_MATRICULA: 'bg-slate-100 text-slate-600',
  EM_ANALISE: 'bg-sky-50 text-sky-700',
  APROVADA: 'bg-emerald-50 text-emerald-700',
  AGUARDANDO_PAGAMENTO: 'bg-amber-50 text-amber-700',
  ATIVA: 'bg-emerald-100 text-emerald-800',
  REJEITADA: 'bg-red-50 text-red-700',
  CANCELADA: 'bg-slate-100 text-slate-400',
}

export function MatriculaPage() {
  const { filhoAtivo } = useFilho()
  const [matriculas, setMatriculas] = useState<MatriculaRead[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [criando, setCriando] = useState(false)
  const [cancelandoId, setCancelandoId] = useState<number | null>(null)
  const [uploadTarget, setUploadTarget] = useState<{ matriculaId: number; tipo: string } | null>(
    null,
  )

  function reload() {
    setLoading(true)
    setErro(null)
    matriculasApi
      .listar({ limit: 100 })
      .then((p) => setMatriculas(p.items))
      .catch((err) => setErro(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(reload, [])

  const minhasMatriculas = filhoAtivo
    ? matriculas.filter((m) => m.aluno_id === filhoAtivo.id)
    : matriculas

  async function cancelar(matriculaId: number) {
    const motivo = window.prompt('Motivo do cancelamento (mínimo 5 caracteres):')
    if (!motivo || motivo.trim().length < 5) return
    setCancelandoId(matriculaId)
    try {
      await matriculasApi.cancelar(matriculaId, motivo.trim())
      reload()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setCancelandoId(null)
    }
  }

  async function handleUpload(file: File) {
    if (!uploadTarget) return
    try {
      await matriculasApi.uploadDocumento(uploadTarget.matriculaId, uploadTarget.tipo, file)
      setUploadTarget(null)
      reload()
    } catch (err) {
      setErro(apiErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title="Matrícula"
        subtitle={filhoAtivo ? `Matrículas de ${filhoAtivo.nome}` : 'Matrículas da família'}
        action={
          <button
            onClick={() => setCriando(true)}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            <Plus size={16} />
            Nova pré-matrícula
          </button>
        }
      />

      {erro && (
        <p className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{erro}</p>
      )}

      {loading ? (
        <div className="flex justify-center py-16 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : (
        <div className="space-y-4">
          {minhasMatriculas.map((m) => (
            <div key={m.id} className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="mb-3 flex items-start justify-between">
                <div>
                  <p className="font-semibold text-slate-900">
                    {m.aluno_nome} · {m.serie_label} · {TURNO_LABELS[m.turno]} · {m.ano_letivo}
                  </p>
                  <p className="text-xs text-slate-400">
                    Criada em {new Date(m.created_at).toLocaleDateString('pt-BR')}
                    {m.turma_nome ? ` · Turma: ${m.turma_nome}` : ''}
                  </p>
                </div>
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_COLOR[m.status]}`}
                >
                  {STATUS_MATRICULA_LABELS[m.status]}
                </span>
              </div>

              {m.motivo_rejeicao && (
                <p className="mb-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
                  Motivo da rejeição: {m.motivo_rejeicao}
                </p>
              )}
              {m.motivo_cancelamento && (
                <p className="mb-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
                  Motivo do cancelamento: {m.motivo_cancelamento}
                </p>
              )}

              <div className="mb-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                {m.documentos.map((d) => (
                  <div
                    key={d.tipo}
                    className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-xs"
                  >
                    <span className={d.entregue ? 'text-slate-600' : 'text-amber-700'}>
                      {d.label} {d.entregue ? '✓' : '(pendente)'}
                    </span>
                    {!d.entregue && (m.status === 'PRE_MATRICULA' || m.status === 'EM_ANALISE') && (
                      <button
                        onClick={() => setUploadTarget({ matriculaId: m.id, tipo: d.tipo })}
                        className="flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 font-medium text-emerald-700 hover:bg-emerald-100"
                      >
                        <Upload size={12} />
                        Enviar
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {m.status === 'PRE_MATRICULA' && (
                <button
                  onClick={() => cancelar(m.id)}
                  disabled={cancelandoId === m.id}
                  className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-60"
                >
                  <XCircle size={14} />
                  Cancelar pré-matrícula
                </button>
              )}
            </div>
          ))}
          {minhasMatriculas.length === 0 && (
            <p className="py-8 text-center text-slate-400">Nenhuma matrícula encontrada.</p>
          )}
        </div>
      )}

      {criando && (
        <NovaPreMatriculaModal
          onClose={() => setCriando(false)}
          onSaved={() => {
            setCriando(false)
            reload()
          }}
        />
      )}

      {uploadTarget && (
        <Modal title="Enviar documento" onClose={() => setUploadTarget(null)}>
          <input
            type="file"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleUpload(file)
            }}
            className="input"
          />
        </Modal>
      )}
    </div>
  )
}

function NovaPreMatriculaModal({
  onClose,
  onSaved,
}: {
  onClose: () => void
  onSaved: () => void
}) {
  const { filhoAtivo } = useFilho()
  const [modo, setModo] = useState<'existente' | 'novo'>(filhoAtivo ? 'existente' : 'novo')
  const [nome, setNome] = useState('')
  const [dataNascimento, setDataNascimento] = useState('')
  const [cpfAluno, setCpfAluno] = useState('')
  const [anoLetivo, setAnoLetivo] = useState(new Date().getFullYear())
  const [serie, setSerie] = useState<Serie>('INFANTIL_1')
  const [turno, setTurno] = useState<Turno>('MANHA')
  const [observacoes, setObservacoes] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await matriculasApi.criar({
        aluno_id: modo === 'existente' ? filhoAtivo?.id ?? null : null,
        aluno:
          modo === 'novo'
            ? { nome, data_nascimento: dataNascimento, cpf: cpfAluno || null }
            : null,
        ano_letivo: anoLetivo,
        serie,
        turno,
        observacoes: observacoes || null,
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Nova pré-matrícula" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {filhoAtivo && (
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Aluno</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setModo('existente')}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm ${
                  modo === 'existente'
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                    : 'border-slate-200 text-slate-600'
                }`}
              >
                {filhoAtivo.nome} (rematrícula)
              </button>
              <button
                type="button"
                onClick={() => setModo('novo')}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm ${
                  modo === 'novo'
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                    : 'border-slate-200 text-slate-600'
                }`}
              >
                Novo aluno
              </button>
            </div>
          </div>
        )}

        {modo === 'novo' && (
          <>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Nome do aluno
              </label>
              <input
                required
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                className="input"
              />
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
                  value={cpfAluno}
                  onChange={(e) => setCpfAluno(e.target.value)}
                  className="input"
                />
              </div>
            </div>
          </>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
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
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Série</label>
            <select value={serie} onChange={(e) => setSerie(e.target.value as Serie)} className="input">
              {Object.entries(SERIE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Turno</label>
            <select value={turno} onChange={(e) => setTurno(e.target.value as Turno)} className="input">
              {Object.entries(TURNO_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Observações (opcional)
          </label>
          <textarea
            rows={3}
            value={observacoes}
            onChange={(e) => setObservacoes(e.target.value)}
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
            {salvando ? 'Enviando...' : 'Enviar pré-matrícula'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
