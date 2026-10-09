import { useCallback, useEffect, useRef, useState } from 'react'
import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Clock,
  Loader2,
  MessageSquarePlus,
  Send,
  Sparkles,
  X,
  XCircle,
} from 'lucide-react'
import { assistenteApi } from '../api/assistente'
import { apiErrorMessage } from '../api/client'
import type { AcaoRead, MensagemRead } from '../types/assistente'

const STORAGE_KEY = 'assistente_conversa_id'
export const EVENTO_ACAO_CONFIRMADA = 'assistente:acao-confirmada'

const SUGESTOES = [
  'Como funciona a matrícula?',
  'Quais matrículas estão em análise?',
  'Mostre o boletim de um aluno',
  'Quem está inadimplente?',
]

function lerConversaSalva(): number | null {
  try {
    const valor = localStorage.getItem(STORAGE_KEY)
    return valor ? Number(valor) : null
  } catch {
    return null
  }
}

function salvarConversa(id: number | null) {
  try {
    if (id === null) localStorage.removeItem(STORAGE_KEY)
    else localStorage.setItem(STORAGE_KEY, String(id))
  } catch {
    /* sem storage: segue sem persistir */
  }
}

function hora(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

export function ChatAssistente() {
  const [aberto, setAberto] = useState(false)
  const [conversaId, setConversaId] = useState<number | null>(null)
  const [mensagens, setMensagens] = useState<MensagemRead[]>([])
  const [texto, setTexto] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [decidindo, setDecidindo] = useState<string | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [carregado, setCarregado] = useState(false)
  const fimRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Ao abrir pela primeira vez, retoma a última conversa (se ainda existir).
  useEffect(() => {
    if (!aberto || carregado) return
    setCarregado(true)
    const salvo = lerConversaSalva()
    if (salvo === null) return
    assistenteApi
      .buscarConversa(salvo)
      .then((c) => {
        setConversaId(c.id)
        setMensagens(c.mensagens)
      })
      .catch(() => salvarConversa(null))
  }, [aberto, carregado])

  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mensagens, enviando, aberto])

  useEffect(() => {
    if (aberto) inputRef.current?.focus()
  }, [aberto])

  const novaConversa = useCallback(() => {
    setConversaId(null)
    setMensagens([])
    setErro(null)
    salvarConversa(null)
  }, [])

  async function enviar(conteudo: string) {
    const limpo = conteudo.trim()
    if (!limpo || enviando) return
    setErro(null)
    setTexto('')
    setEnviando(true)

    const otimista: MensagemRead = {
      id: -Date.now(),
      role: 'user',
      conteudo: limpo,
      created_at: new Date().toISOString(),
      acao: null,
    }
    setMensagens((atual) => [...atual, otimista])

    try {
      let id = conversaId
      if (id === null) {
        const nova = await assistenteApi.criarConversa()
        id = nova.id
        setConversaId(id)
        salvarConversa(id)
      }
      const resposta = await assistenteApi.enviarMensagem(id, limpo)
      setMensagens((atual) => [...atual.filter((m) => m.id !== otimista.id), ...resposta.mensagens])
    } catch (e) {
      setErro(apiErrorMessage(e))
    } finally {
      setEnviando(false)
    }
  }

  async function decidir(acao: AcaoRead, confirmar: boolean) {
    setDecidindo(acao.id)
    setErro(null)
    try {
      const decisao = confirmar
        ? await assistenteApi.confirmarAcao(acao.id)
        : await assistenteApi.cancelarAcao(acao.id)
      setMensagens((atual) => [
        ...atual.map((m) => (m.acao?.id === acao.id ? { ...m, acao: decisao.acao } : m)),
        ...decisao.mensagens,
      ])
      if (confirmar && decisao.acao.status === 'CONFIRMADA') {
        window.dispatchEvent(new CustomEvent(EVENTO_ACAO_CONFIRMADA))
      }
    } catch (e) {
      setErro(apiErrorMessage(e))
      // o estado pode ter mudado (expirou/já decidida): recarrega a conversa
      if (conversaId !== null) {
        assistenteApi
          .buscarConversa(conversaId)
          .then((c) => setMensagens(c.mensagens))
          .catch(() => undefined)
      }
    } finally {
      setDecidindo(null)
    }
  }

  return (
    <>
      {!aberto && (
        <button
          onClick={() => setAberto(true)}
          aria-label="Abrir assistente"
          className="fixed bottom-5 right-5 z-40 flex items-center gap-2 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-700 px-4 py-3 text-sm font-semibold text-white shadow-lift ring-1 ring-white/20 transition-transform hover:scale-[1.03]"
        >
          <Sparkles size={18} />
          <span className="hidden sm:inline">Assistente</span>
        </button>
      )}

      {aberto && (
        <section
          aria-label="Assistente de IA"
          className="fixed inset-0 z-50 flex flex-col bg-white shadow-lift ring-1 ring-slate-900/10 sm:inset-auto sm:bottom-5 sm:right-5 sm:h-[36rem] sm:w-[26rem] sm:rounded-2xl"
        >
          <header className="flex items-center gap-3 border-b border-slate-100 bg-emerald-950 px-4 py-3 text-white sm:rounded-t-2xl">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600">
              <Sparkles size={16} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold leading-tight">Assistente Semeando</p>
              <p className="text-[11px] leading-tight text-emerald-200/70">
                Consulta dados e executa ações com a sua confirmação
              </p>
            </div>
            <button
              onClick={novaConversa}
              title="Nova conversa"
              aria-label="Nova conversa"
              className="rounded-lg p-1.5 text-emerald-100/80 hover:bg-white/10"
            >
              <MessageSquarePlus size={17} />
            </button>
            <button
              onClick={() => setAberto(false)}
              aria-label="Fechar assistente"
              className="rounded-lg p-1.5 text-emerald-100/80 hover:bg-white/10"
            >
              <X size={18} />
            </button>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto bg-slate-50 px-4 py-4">
            {mensagens.length === 0 && !enviando && (
              <div className="pt-4 text-center">
                <p className="font-display text-base font-semibold text-slate-800">
                  Como posso ajudar?
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Pergunte sobre o sistema ou peça para consultar e alterar dados.
                </p>
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  {SUGESTOES.map((s) => (
                    <button
                      key={s}
                      onClick={() => enviar(s)}
                      className="rounded-full border border-emerald-200 bg-white px-3 py-1.5 text-xs font-medium text-emerald-800 hover:bg-emerald-50"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {mensagens.map((m) =>
              m.role === 'acao' && m.acao ? (
                <CartaoAcao
                  key={m.id}
                  acao={m.acao}
                  ocupado={decidindo === m.acao.id}
                  onConfirmar={() => decidir(m.acao!, true)}
                  onCancelar={() => decidir(m.acao!, false)}
                />
              ) : (
                <Balao key={m.id} mensagem={m} />
              ),
            )}

            {enviando && (
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Loader2 size={14} className="animate-spin" />
                Pensando...
              </div>
            )}

            {erro && (
              <div className="flex items-start gap-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700 ring-1 ring-red-200">
                <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                <span>{erro}</span>
              </div>
            )}
            <div ref={fimRef} />
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              void enviar(texto)
            }}
            className="flex items-end gap-2 border-t border-slate-100 bg-white p-3 sm:rounded-b-2xl"
          >
            <textarea
              ref={inputRef}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  void enviar(texto)
                }
              }}
              rows={1}
              maxLength={2000}
              placeholder="Escreva sua mensagem..."
              className="max-h-28 min-h-[2.5rem] flex-1 resize-none rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none focus:border-emerald-500 focus:bg-white"
            />
            <button
              type="submit"
              disabled={enviando || !texto.trim()}
              aria-label="Enviar"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              <Send size={16} />
            </button>
          </form>
        </section>
      )}
    </>
  )
}

// Estilos do markdown das respostas do assistente (tabelas, listas, negrito, código).
const markdownComponents: Components = {
  p: ({ children }) => <p className="my-1.5 first:mt-0 last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
  ul: ({ children }) => <ul className="my-1.5 list-disc space-y-0.5 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="my-1.5 list-decimal space-y-0.5 pl-5">{children}</ol>,
  h1: ({ children }) => <h3 className="mb-1 mt-2 text-base font-semibold">{children}</h3>,
  h2: ({ children }) => <h3 className="mb-1 mt-2 text-base font-semibold">{children}</h3>,
  h3: ({ children }) => <h4 className="mb-1 mt-2 text-sm font-semibold">{children}</h4>,
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noreferrer" className="text-emerald-700 underline">
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded bg-slate-100 px-1 py-0.5 text-[12px] text-slate-800">{children}</code>
  ),
  hr: () => <hr className="my-2 border-slate-200" />,
  table: ({ children }) => (
    <div className="my-2 overflow-x-auto rounded-lg ring-1 ring-slate-200">
      <table className="w-full border-collapse text-left text-xs">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-emerald-50 text-emerald-900">{children}</thead>,
  th: ({ children }) => <th className="whitespace-nowrap px-2.5 py-1.5 font-semibold">{children}</th>,
  td: ({ children }) => (
    <td className="whitespace-nowrap border-t border-slate-100 px-2.5 py-1.5">{children}</td>
  ),
}

function Balao({ mensagem }: { mensagem: MensagemRead }) {
  const meu = mensagem.role === 'user'
  return (
    <div className={`flex ${meu ? 'justify-end' : 'justify-start'}`}>
      {meu ? (
        <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-emerald-600 px-3.5 py-2 text-sm leading-relaxed text-white">
          {mensagem.conteudo}
        </div>
      ) : (
        <div className="min-w-0 max-w-[92%] rounded-2xl rounded-bl-md bg-white px-3.5 py-2 text-sm leading-relaxed text-slate-800 shadow-card ring-1 ring-slate-200">
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {mensagem.conteudo ?? ''}
          </ReactMarkdown>
        </div>
      )}
    </div>
  )
}

function CartaoAcao({
  acao,
  ocupado,
  onConfirmar,
  onCancelar,
}: {
  acao: AcaoRead
  ocupado: boolean
  onConfirmar: () => void
  onCancelar: () => void
}) {
  const expirou = acao.status === 'PENDENTE' && new Date(acao.expira_em).getTime() <= Date.now()
  const pendente = acao.status === 'PENDENTE' && !expirou
  const borda = acao.destrutiva ? 'border-red-200 bg-red-50/60' : 'border-emerald-200 bg-white'

  return (
    <div className={`rounded-xl border p-3.5 shadow-card ${borda}`}>
      <div className="mb-2 flex items-center gap-2">
        {acao.destrutiva ? (
          <AlertTriangle size={15} className="text-red-600" />
        ) : (
          <Sparkles size={15} className="text-emerald-600" />
        )}
        <p className="text-sm font-semibold text-slate-900">{acao.titulo}</p>
        <span className="ml-auto">
          <EstadoAcao acao={acao} expirou={expirou} />
        </span>
      </div>

      <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-slate-700">
        {acao.resumo}
      </p>

      {acao.erro && (
        <p className="mt-2 rounded-md bg-red-100 px-2 py-1 text-xs text-red-700">{acao.erro}</p>
      )}

      {pendente && (
        <div className="mt-3 flex items-center gap-2">
          <button
            onClick={onConfirmar}
            disabled={ocupado}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold text-white transition-colors disabled:opacity-60 ${
              acao.destrutiva ? 'bg-red-600 hover:bg-red-700' : 'bg-emerald-600 hover:bg-emerald-700'
            }`}
          >
            {ocupado ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />}
            Confirmar
          </button>
          <button
            onClick={onCancelar}
            disabled={ocupado}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          >
            <X size={15} />
            Cancelar
          </button>
        </div>
      )}
      {pendente && (
        <p className="mt-2 flex items-center gap-1 text-[11px] text-slate-400">
          <Clock size={11} /> Expira às {hora(acao.expira_em)}
        </p>
      )}
    </div>
  )
}

function EstadoAcao({ acao, expirou }: { acao: AcaoRead; expirou: boolean }) {
  if (acao.status === 'CONFIRMADA')
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-emerald-700">
        <CheckCircle2 size={13} /> Executada
      </span>
    )
  if (acao.status === 'CANCELADA')
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-slate-500">
        <XCircle size={13} /> Cancelada
      </span>
    )
  if (acao.status === 'FALHOU')
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-red-700">
        <AlertTriangle size={13} /> Falhou
      </span>
    )
  if (acao.status === 'EXPIRADA' || expirou)
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-amber-600">
        <Clock size={13} /> Expirada
      </span>
    )
  return <span className="text-xs font-medium text-emerald-700">Aguardando você</span>
}
