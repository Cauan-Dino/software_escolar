export type StatusAcao = 'PENDENTE' | 'CONFIRMADA' | 'CANCELADA' | 'EXPIRADA' | 'FALHOU'

export interface AcaoRead {
  id: string
  ferramenta: string
  titulo: string
  resumo: string
  destrutiva: boolean
  status: StatusAcao
  expira_em: string
  decidida_em: string | null
  resultado: Record<string, unknown> | null
  erro: string | null
}

export interface MensagemRead {
  id: number
  role: 'user' | 'assistant' | 'acao'
  conteudo: string | null
  created_at: string
  acao: AcaoRead | null
}

export interface ConversaRead {
  id: number
  titulo: string
  created_at: string
  updated_at: string
}

export interface ConversaDetalhe extends ConversaRead {
  mensagens: MensagemRead[]
}

export interface RespostaChat {
  conversa_id: number
  mensagens: MensagemRead[]
}

export interface DecisaoAcao {
  acao: AcaoRead
  mensagens: MensagemRead[]
}
