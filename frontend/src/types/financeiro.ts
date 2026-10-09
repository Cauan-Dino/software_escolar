export type TipoCobranca = 'MATRICULA' | 'MENSALIDADE' | 'TAXA_EXTRA'

export type StatusCobranca = 'PENDENTE' | 'PAGA' | 'ATRASADA' | 'CANCELADA'

export const TIPO_COBRANCA_LABELS: Record<TipoCobranca, string> = {
  MATRICULA: 'Matrícula',
  MENSALIDADE: 'Mensalidade',
  TAXA_EXTRA: 'Taxa extra',
}

export const STATUS_COBRANCA_LABELS: Record<StatusCobranca, string> = {
  PENDENTE: 'Pendente',
  PAGA: 'Paga',
  ATRASADA: 'Atrasada',
  CANCELADA: 'Cancelada',
}

export interface CobrancaRead {
  id: number
  aluno_id: number
  matricula_id: number | null
  tipo: TipoCobranca
  competencia: string | null
  valor_original: string
  valor_desconto: string
  valor_final: string
  vencimento: string
  status: StatusCobranca
  pago_em: string | null
  gateway_referencia: string | null
  criado_em: string
}

export interface CobrancaCreate {
  aluno_id: number
  tipo: TipoCobranca
  competencia?: string | null
  valor_original: number
  vencimento: string
  matricula_id?: number | null
}

export interface BolsaRead {
  id: number
  aluno_id: number
  percentual_desconto: string
  motivo: string
  vigencia_inicio: string
  vigencia_fim: string | null
}

export interface BolsaCreate {
  aluno_id: number
  percentual_desconto: number
  motivo: string
  vigencia_inicio: string
  vigencia_fim?: string | null
}

export interface TabelaPrecoRead {
  id: number
  serie: string
  ano_letivo: number
  valor_matricula: string
  valor_mensalidade: string
}

export interface TabelaPrecoCreate {
  serie: string
  ano_letivo: number
  valor_matricula: number
  valor_mensalidade: number
}
