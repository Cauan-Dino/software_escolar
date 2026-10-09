export type Role = 'ADMIN' | 'SECRETARIA' | 'FINANCEIRO' | 'PROFESSOR' | 'RESPONSAVEL'

export interface Page<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

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

// --- turmas --------------------------------------------------------------

export type Serie =
  | 'MATERNAL_1'
  | 'MATERNAL_2'
  | 'INFANTIL_1'
  | 'INFANTIL_2'
  | 'ANO_1'
  | 'ANO_2'
  | 'ANO_3'
  | 'ANO_4'
  | 'ANO_5'

export type Turno = 'MANHA' | 'TARDE' | 'INTEGRAL'

export const TURNO_LABELS: Record<Turno, string> = {
  MANHA: 'Manhã',
  TARDE: 'Tarde',
  INTEGRAL: 'Integral',
}

export interface ProfessorResumo {
  id: number
  nome: string
}

export interface TurmaRead {
  id: number
  serie: Serie
  ano_letivo: number
  turno: Turno
  capacidade: number
  vagas_ocupadas: number
  ativa: boolean
  professores: ProfessorResumo[]
  nome: string
  segmento: string
  vagas_disponiveis: number
}

// --- notas -----------------------------------------------------------------

export type Periodo = 'BIMESTRE_1' | 'BIMESTRE_2' | 'BIMESTRE_3' | 'BIMESTRE_4'

export const PERIODO_LABELS: Record<Periodo, string> = {
  BIMESTRE_1: '1º Bimestre',
  BIMESTRE_2: '2º Bimestre',
  BIMESTRE_3: '3º Bimestre',
  BIMESTRE_4: '4º Bimestre',
}

export interface NotaUpsert {
  disciplina: string
  periodo: Periodo
  valor: number
  observacao?: string | null
}

export interface GradeCelula {
  nota_id: number | null
  aluno_id: number
  aluno_nome: string
  disciplina: string
  periodo: Periodo
  valor: number | null
  observacao: string | null
}

export interface TurmaGradeRead {
  turma_id: number
  periodo: Periodo
  disciplinas: string[]
  celulas: GradeCelula[]
}

// --- frequência --------------------------------------------------------

export type StatusFrequencia = 'PRESENTE' | 'FALTA' | 'FALTA_JUSTIFICADA'

export const STATUS_FREQUENCIA_LABELS: Record<StatusFrequencia, string> = {
  PRESENTE: 'Presente',
  FALTA: 'Falta',
  FALTA_JUSTIFICADA: 'Falta justificada',
}

export interface AlunoChamada {
  aluno_id: number
  aluno_nome: string
  status: StatusFrequencia
  observacao: string | null
  lancado: boolean
}

export interface RegistroFrequenciaInput {
  aluno_id: number
  status: StatusFrequencia
  observacao?: string | null
}

// --- comunicação -------------------------------------------------------

export type PublicoAlvo = 'TODOS' | 'TURMA' | 'RESPONSAVEIS' | 'PROFESSORES'

export const PUBLICO_ALVO_LABELS: Record<PublicoAlvo, string> = {
  TODOS: 'Todos',
  TURMA: 'Turma específica',
  RESPONSAVEIS: 'Responsáveis',
  PROFESSORES: 'Professores',
}

export interface AvisoCreate {
  titulo: string
  corpo: string
  publico_alvo: PublicoAlvo
  turma_id?: number | null
  fixado?: boolean
}

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

// --- calendário --------------------------------------------------------

export type TipoEvento = 'PROVA' | 'FERIADO' | 'REUNIAO' | 'EVENTO' | 'OUTRO'

export const TIPO_EVENTO_LABELS: Record<TipoEvento, string> = {
  PROVA: 'Prova',
  FERIADO: 'Feriado',
  REUNIAO: 'Reunião',
  EVENTO: 'Evento',
  OUTRO: 'Outro',
}

export interface EventoCalendarioCreate {
  titulo: string
  descricao?: string | null
  data_inicio: string
  data_fim?: string | null
  tipo: TipoEvento
  turma_id?: number | null
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
