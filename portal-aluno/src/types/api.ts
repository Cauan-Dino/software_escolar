export type Role = 'ADMIN' | 'SECRETARIA' | 'FINANCEIRO' | 'PROFESSOR' | 'RESPONSAVEL' | 'ALUNO'

export interface UserRead {
  id: number
  email: string
  nome: string
  role: Role
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserRead
}

// --- pessoas / aluno --------------------------------------------------------

export interface VinculoRead {
  responsavel_id: number
  nome: string
  parentesco: string
  responsavel_financeiro: boolean
  pode_buscar: boolean
}

export interface AlunoRead {
  id: number
  user_id: number | null
  nome: string
  data_nascimento: string
  cpf: string | null
  responsaveis: VinculoRead[]
}

// --- notas / boletim ---------------------------------------------------------

export type Periodo = 'BIMESTRE_1' | 'BIMESTRE_2' | 'BIMESTRE_3' | 'BIMESTRE_4'

export const PERIODO_LABELS: Record<Periodo, string> = {
  BIMESTRE_1: '1º Bimestre',
  BIMESTRE_2: '2º Bimestre',
  BIMESTRE_3: '3º Bimestre',
  BIMESTRE_4: '4º Bimestre',
}

export interface NotaPeriodo {
  periodo: Periodo
  valor: number
  observacao: string | null
}

export interface BoletimDisciplina {
  disciplina: string
  notas: NotaPeriodo[]
  media: number | null
  situacao: string
}

export interface BoletimRead {
  aluno_id: number
  disciplinas: BoletimDisciplina[]
}

// --- frequência --------------------------------------------------------------

export type StatusFrequencia = 'PRESENTE' | 'FALTA' | 'FALTA_JUSTIFICADA'

export const STATUS_FREQUENCIA_LABELS: Record<StatusFrequencia, string> = {
  PRESENTE: 'Presente',
  FALTA: 'Falta',
  FALTA_JUSTIFICADA: 'Falta justificada',
}

export interface FrequenciaRead {
  id: number
  aluno_id: number
  turma_id: number
  data: string
  status: StatusFrequencia
  observacao: string | null
}

export interface HistoricoFrequencia {
  aluno_id: number
  de: string
  ate: string
  percentual_presenca: number
  registros: FrequenciaRead[]
}

// --- financeiro ----------------------------------------------------------------

export type StatusCobranca = 'PENDENTE' | 'PAGA' | 'ATRASADA' | 'CANCELADA'

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
  tipo: string
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

export interface Page<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

// --- comunicação -----------------------------------------------------------

export type PublicoAlvo = 'TODOS' | 'TURMA' | 'RESPONSAVEIS' | 'PROFESSORES'

export interface AvisoRead {
  id: number
  titulo: string
  corpo: string
  publico_alvo: PublicoAlvo
  turma_id: number | null
  fixado: boolean
  publicado_por_user_id: number
  publicado_em: string
  lido: boolean
}

// --- calendário --------------------------------------------------------------

export type TipoEvento = 'PROVA' | 'FERIADO' | 'REUNIAO' | 'EVENTO' | 'OUTRO'

export const TIPO_EVENTO_LABELS: Record<TipoEvento, string> = {
  PROVA: 'Prova',
  FERIADO: 'Feriado',
  REUNIAO: 'Reunião',
  EVENTO: 'Evento',
  OUTRO: 'Outro',
}

export interface EventoCalendarioRead {
  id: number
  titulo: string
  descricao: string | null
  data_inicio: string
  data_fim: string | null
  tipo: TipoEvento
  turma_id: number | null
  criado_por_user_id: number
}
