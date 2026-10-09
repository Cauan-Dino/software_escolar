import { useState } from 'react'
import { Plus, CheckCircle2 } from 'lucide-react'
import {
  criarBolsa,
  criarCobranca,
  gerarMensalidades,
  listarBolsas,
  listarCobrancas,
  listarPrecos,
  marcarPaga,
  salvarPreco,
} from '../api/financeiro'
import { apiErrorMessage } from '../api/client'
import { usePaginatedList } from '../lib/usePaginatedList'
import { useAsyncList } from '../lib/useAsyncList'
import { PageHeader } from '../components/PageHeader'
import { Modal } from '../components/Modal'
import { ErrorBanner, ErrorRow, LoadingRow } from '../components/AsyncState'
import { Pagination } from '../components/Pagination'
import type { BolsaRead, CobrancaRead, StatusCobranca, TabelaPrecoRead } from '../types/financeiro'
import { STATUS_COBRANCA_LABELS, TIPO_COBRANCA_LABELS } from '../types/financeiro'

type Aba = 'cobrancas' | 'bolsas' | 'precos'

const STATUS_STYLE: Record<StatusCobranca, string> = {
  PENDENTE: 'bg-amber-50 text-amber-700',
  PAGA: 'bg-emerald-50 text-emerald-700',
  ATRASADA: 'bg-red-50 text-red-700',
  CANCELADA: 'bg-slate-100 text-slate-500',
}

function formatMoeda(valor: string) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function FinanceiroPage() {
  const [aba, setAba] = useState<Aba>('cobrancas')

  return (
    <div>
      <PageHeader title="Financeiro" subtitle="Cobranças, bolsas e tabela de preços" />

      <div className="mb-6 flex gap-2 border-b border-slate-200">
        {(
          [
            ['cobrancas', 'Cobranças'],
            ['bolsas', 'Bolsas'],
            ['precos', 'Preços'],
          ] as [Aba, string][]
        ).map(([valor, label]) => (
          <button
            key={valor}
            onClick={() => setAba(valor)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
              aba === valor
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {aba === 'cobrancas' && <AbaCobrancas />}
      {aba === 'bolsas' && <AbaBolsas />}
      {aba === 'precos' && <AbaPrecos />}
    </div>
  )
}

// --- Aba Cobranças --------------------------------------------------------------------------

function AbaCobrancas() {
  const [filtro, setFiltro] = useState<StatusCobranca | 'todas'>('todas')
  const [gerandoMensalidades, setGerandoMensalidades] = useState(false)
  const [criando, setCriando] = useState(false)

  const { data, total, loading, error, reload, offset, pageSize, hasPrev, hasNext, goPrev, goNext } =
    usePaginatedList<CobrancaRead>(
      ({ limit, offset }) =>
        listarCobrancas({ limit, offset, status: filtro === 'todas' ? undefined : filtro }),
      [filtro],
    )

  async function handleMarcarPaga(c: CobrancaRead) {
    try {
      await marcarPaga(c.id)
      reload()
    } catch (err) {
      alert(apiErrorMessage(err))
    }
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          {(['todas', ...Object.keys(STATUS_COBRANCA_LABELS)] as (StatusCobranca | 'todas')[]).map(
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
                {s === 'todas' ? 'Todas' : STATUS_COBRANCA_LABELS[s]}
              </button>
            ),
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setGerandoMensalidades(true)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Gerar mensalidades do mês
          </button>
          <button
            onClick={() => setCriando(true)}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
          >
            <Plus size={16} />
            Nova cobrança
          </button>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full min-w-[34rem] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-5 py-3 font-medium">Aluno</th>
              <th className="px-5 py-3 font-medium">Tipo</th>
              <th className="px-5 py-3 font-medium">Competência</th>
              <th className="px-5 py-3 font-medium">Valor</th>
              <th className="px-5 py-3 font-medium">Vencimento</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && <LoadingRow colSpan={7} />}
            {!loading && error && <ErrorRow colSpan={7} message={error} />}
            {!loading &&
              !error &&
              data.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-medium text-slate-900">#{c.aluno_id}</td>
                  <td className="px-5 py-3 text-slate-600">{TIPO_COBRANCA_LABELS[c.tipo]}</td>
                  <td className="px-5 py-3 text-slate-600">{c.competencia ?? '-'}</td>
                  <td className="px-5 py-3 text-slate-600">
                    {formatMoeda(c.valor_final)}
                    {Number(c.valor_desconto) > 0 && (
                      <span className="ml-1 text-xs text-slate-400">
                        (desc. {formatMoeda(c.valor_desconto)})
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {new Date(c.vencimento).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_STYLE[c.status]}`}
                    >
                      {STATUS_COBRANCA_LABELS[c.status]}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    {(c.status === 'PENDENTE' || c.status === 'ATRASADA') && (
                      <button
                        onClick={() => handleMarcarPaga(c)}
                        title="Marcar como paga"
                        className="rounded-md p-1.5 text-slate-400 hover:bg-emerald-50 hover:text-emerald-600"
                      >
                        <CheckCircle2 size={16} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            {!loading && !error && data.length === 0 && (
              <tr>
                <td colSpan={7} className="px-5 py-8 text-center text-slate-400">
                  Nenhuma cobrança encontrada.
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

      {gerandoMensalidades && (
        <GerarMensalidadesForm
          onClose={() => setGerandoMensalidades(false)}
          onSaved={() => {
            setGerandoMensalidades(false)
            reload()
          }}
        />
      )}
      {criando && (
        <CriarCobrancaForm
          onClose={() => setCriando(false)}
          onSaved={() => {
            setCriando(false)
            reload()
          }}
        />
      )}
    </div>
  )
}

function GerarMensalidadesForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const hoje = new Date()
  const competenciaPadrao = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}`
  const [competencia, setCompetencia] = useState(competenciaPadrao)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [resultado, setResultado] = useState<number | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      const criadas = await gerarMensalidades(competencia)
      setResultado(criadas.length)
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Gerar mensalidades do mês" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Competência (AAAA-MM)
          </label>
          <input
            required
            pattern="\d{4}-\d{2}"
            value={competencia}
            onChange={(e) => setCompetencia(e.target.value)}
            placeholder="2026-03"
            className="input"
          />
        </div>

        {erro && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>}
        {resultado !== null && (
          <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
            {resultado} mensalidade(s) gerada(s).
          </p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
          >
            Fechar
          </button>
          <button
            type="submit"
            disabled={salvando}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {salvando ? 'Gerando...' : 'Gerar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function CriarCobrancaForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [alunoId, setAlunoId] = useState('')
  const [tipo, setTipo] = useState<'MATRICULA' | 'TAXA_EXTRA'>('TAXA_EXTRA')
  const [valor, setValor] = useState('')
  const [vencimento, setVencimento] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await criarCobranca({
        aluno_id: Number(alunoId),
        tipo,
        valor_original: Number(valor),
        vencimento,
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Nova cobrança avulsa" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">ID do aluno</label>
          <input
            required
            type="number"
            value={alunoId}
            onChange={(e) => setAlunoId(e.target.value)}
            className="input"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Tipo</label>
            <select
              value={tipo}
              onChange={(e) => setTipo(e.target.value as 'MATRICULA' | 'TAXA_EXTRA')}
              className="input"
            >
              <option value="MATRICULA">Matrícula</option>
              <option value="TAXA_EXTRA">Taxa extra</option>
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Valor (R$)</label>
            <input
              required
              type="number"
              step="0.01"
              min="0.01"
              value={valor}
              onChange={(e) => setValor(e.target.value)}
              className="input"
            />
          </div>
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Vencimento</label>
          <input
            required
            type="date"
            value={vencimento}
            onChange={(e) => setVencimento(e.target.value)}
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
            {salvando ? 'Salvando...' : 'Criar cobrança'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// --- Aba Bolsas -----------------------------------------------------------------------------

function AbaBolsas() {
  const [criando, setCriando] = useState(false)
  const {
    data: bolsas,
    loading,
    error,
    reload,
  } = useAsyncList<BolsaRead>(() => listarBolsas(), [])

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <button
          onClick={() => setCriando(true)}
          className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          <Plus size={16} />
          Nova bolsa
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full min-w-[34rem] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-5 py-3 font-medium">Aluno</th>
              <th className="px-5 py-3 font-medium">Desconto</th>
              <th className="px-5 py-3 font-medium">Motivo</th>
              <th className="px-5 py-3 font-medium">Vigência</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && <LoadingRow colSpan={4} />}
            {!loading && error && <ErrorRow colSpan={4} message={error} />}
            {!loading &&
              !error &&
              bolsas.map((b) => (
                <tr key={b.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-medium text-slate-900">#{b.aluno_id}</td>
                  <td className="px-5 py-3 text-slate-600">{Number(b.percentual_desconto)}%</td>
                  <td className="px-5 py-3 text-slate-600">{b.motivo}</td>
                  <td className="px-5 py-3 text-slate-600">
                    {new Date(b.vigencia_inicio).toLocaleDateString('pt-BR')} —{' '}
                    {b.vigencia_fim ? new Date(b.vigencia_fim).toLocaleDateString('pt-BR') : 'sem fim'}
                  </td>
                </tr>
              ))}
            {!loading && !error && bolsas.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-slate-400">
                  Nenhuma bolsa cadastrada.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {criando && (
        <CriarBolsaForm
          onClose={() => setCriando(false)}
          onSaved={() => {
            setCriando(false)
            reload()
          }}
        />
      )}
    </div>
  )
}

function CriarBolsaForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [alunoId, setAlunoId] = useState('')
  const [percentual, setPercentual] = useState('')
  const [motivo, setMotivo] = useState('')
  const [vigenciaInicio, setVigenciaInicio] = useState('')
  const [vigenciaFim, setVigenciaFim] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await criarBolsa({
        aluno_id: Number(alunoId),
        percentual_desconto: Number(percentual),
        motivo,
        vigencia_inicio: vigenciaInicio,
        vigencia_fim: vigenciaFim || null,
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Nova bolsa" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">ID do aluno</label>
          <input
            required
            type="number"
            value={alunoId}
            onChange={(e) => setAlunoId(e.target.value)}
            className="input"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Percentual de desconto
          </label>
          <input
            required
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={percentual}
            onChange={(e) => setPercentual(e.target.value)}
            className="input"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Motivo</label>
          <input
            required
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            className="input"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Vigência início
            </label>
            <input
              required
              type="date"
              value={vigenciaInicio}
              onChange={(e) => setVigenciaInicio(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Vigência fim (opcional)
            </label>
            <input
              type="date"
              value={vigenciaFim}
              onChange={(e) => setVigenciaFim(e.target.value)}
              className="input"
            />
          </div>
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
            {salvando ? 'Salvando...' : 'Criar bolsa'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// --- Aba Preços -----------------------------------------------------------------------------

function AbaPrecos() {
  const [criando, setCriando] = useState(false)
  const {
    data: precos,
    loading,
    error,
    reload,
  } = useAsyncList<TabelaPrecoRead>(() => listarPrecos(), [])

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <button
          onClick={() => setCriando(true)}
          className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          <Plus size={16} />
          Novo preço
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full min-w-[34rem] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-5 py-3 font-medium">Série</th>
              <th className="px-5 py-3 font-medium">Ano letivo</th>
              <th className="px-5 py-3 font-medium">Matrícula</th>
              <th className="px-5 py-3 font-medium">Mensalidade</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && <LoadingRow colSpan={4} />}
            {!loading && error && <ErrorRow colSpan={4} message={error} />}
            {!loading &&
              !error &&
              precos.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-medium text-slate-900">{p.serie}</td>
                  <td className="px-5 py-3 text-slate-600">{p.ano_letivo}</td>
                  <td className="px-5 py-3 text-slate-600">{formatMoeda(p.valor_matricula)}</td>
                  <td className="px-5 py-3 text-slate-600">{formatMoeda(p.valor_mensalidade)}</td>
                </tr>
              ))}
            {!loading && !error && precos.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-slate-400">
                  Nenhum preço cadastrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {criando && (
        <CriarPrecoForm
          onClose={() => setCriando(false)}
          onSaved={() => {
            setCriando(false)
            reload()
          }}
        />
      )}
    </div>
  )
}

function CriarPrecoForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [serie, setSerie] = useState('')
  const [anoLetivo, setAnoLetivo] = useState(new Date().getFullYear())
  const [valorMatricula, setValorMatricula] = useState('')
  const [valorMensalidade, setValorMensalidade] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await salvarPreco({
        serie,
        ano_letivo: anoLetivo,
        valor_matricula: Number(valorMatricula),
        valor_mensalidade: Number(valorMensalidade),
      })
      onSaved()
    } catch (err) {
      setErro(apiErrorMessage(err))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal title="Novo preço" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Série</label>
            <input
              required
              value={serie}
              onChange={(e) => setSerie(e.target.value)}
              placeholder="ANO_1"
              className="input"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Ano letivo</label>
            <input
              required
              type="number"
              value={anoLetivo}
              onChange={(e) => setAnoLetivo(Number(e.target.value))}
              className="input"
            />
          </div>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Valor da matrícula (R$)
            </label>
            <input
              required
              type="number"
              step="0.01"
              min="0"
              value={valorMatricula}
              onChange={(e) => setValorMatricula(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Valor da mensalidade (R$)
            </label>
            <input
              required
              type="number"
              step="0.01"
              min="0"
              value={valorMensalidade}
              onChange={(e) => setValorMensalidade(e.target.value)}
              className="input"
            />
          </div>
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
