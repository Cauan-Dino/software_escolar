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

// --- pessoas / alunos ------------------------------------------------------

export type Parentesco = 'MAE' | 'PAI' | 'AVO' | 'TIO' | 'OUTRO'

export const PARENTESCO_LABELS: Record<Parentesco, string> = {
  MAE: 'Mãe',
  PAI: 'Pai',
  AVO: 'Avô/Avó',
  TIO: 'Tio/Tia',
  OUTRO: 'Outro',
}

export interface VinculoRead {
  responsavel_id: number
  nome: string
  parentesco: Parentesco
  responsavel_financeiro: boolean
  pode_buscar: boolean
}

export interface AlunoRead {
  id: number
  user_id?: number | null
  nome: string
  data_nascimento: string
  cpf: string | null
  responsaveis: VinculoRead[]
}

// --- série / turno -----------------------------------------------------

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

export const SERIE_LABELS: Record<Serie, string> = {
  MATERNAL_1: 'Maternal 1',
  MATERNAL_2: 'Maternal 2',
  INFANTIL_1: 'Infantil 1',
  INFANTIL_2: 'Infantil 2',
  ANO_1: '1º Ano',
  ANO_2: '2º Ano',
  ANO_3: '3º Ano',
  ANO_4: '4º Ano',
  ANO_5: '5º Ano',
}

export type Turno = 'MANHA' | 'TARDE' | 'INTEGRAL'

export const TURNO_LABELS: Record<Turno, string> = {
  MANHA: 'Manhã',
  TARDE: 'Tarde',
  INTEGRAL: 'Integral',
}

// --- notas -----------------------------------------------------------------

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

// --- frequência --------------------------------------------------------

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

// --- financeiro --------------------------------------------------------

export type TipoCobranca = 'MATRICULA' | 'MENSALIDADE' | 'TAXA_EXTRA'

export const TIPO_COBRANCA_LABELS: Record<TipoCobranca, string> = {
  MATRICULA: 'Matrícula',
  MENSALIDADE: 'Mensalidade',
  TAXA_EXTRA: 'Taxa extra',
}

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

// --- comunicação -------------------------------------------------------

export type PublicoAlvo = 'TODOS' | 'TURMA' | 'RESPONSAVEIS' | 'PROFESSORES'

export const PUBLICO_ALVO_LABELS: Record<PublicoAlvo, string> = {
  TODOS: 'Todos',
  TURMA: 'Turma específica',
  RESPONSAVEIS: 'Responsáveis',
  PROFESSORES: 'Professores',
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

// --- matrícula -----------------------------------------------------------

export type StatusMatricula =
  | 'PRE_MATRICULA'
  | 'EM_ANALISE'
  | 'APROVADA'
  | 'AGUARDANDO_PAGAMENTO'
  | 'ATIVA'
  | 'REJEITADA'
  | 'CANCELADA'

export const STATUS_MATRICULA_LABELS: Record<StatusMatricula, string> = {
  PRE_MATRICULA: 'Pré-matrícula',
  EM_ANALISE: 'Em análise',
  APROVADA: 'Aprovada',
  AGUARDANDO_PAGAMENTO: 'Aguardando pagamento',
  ATIVA: 'Ativa',
  REJEITADA: 'Rejeitada',
  CANCELADA: 'Cancelada',
}

export type TipoMatriculaCategoria = 'NOVA' | 'REMATRICULA'

export type TipoDocumento =
  | 'CERTIDAO_NASCIMENTO'
  | 'CARTAO_VACINA'
  | 'COMPROVANTE_RESIDENCIA'
  | 'DOCUMENTO_RESPONSAVEL'

export const TIPO_DOCUMENTO_LABELS: Record<TipoDocumento, string> = {
  CERTIDAO_NASCIMENTO: 'Certidão de nascimento',
  CARTAO_VACINA: 'Cartão de vacina',
  COMPROVANTE_RESIDENCIA: 'Comprovante de residência',
  DOCUMENTO_RESPONSAVEL: 'Documento do responsável',
}

export interface DocumentoRead {
  tipo: TipoDocumento
  entregue: boolean
  arquivo_nome: string | null
  conferido_em: string | null
  label: string
  tem_arquivo: boolean
}

export interface MatriculaRead {
  id: number
  aluno_id: number
  aluno_nome: string
  ano_letivo: number
  serie: Serie
  turno: Turno
  turma_id: number | null
  turma_nome: string | null
  tipo: TipoMatriculaCategoria
  status: StatusMatricula
  tamanho_farda: string | null
  farda_indisponivel: boolean
  observacoes: string | null
  motivo_rejeicao: string | null
  motivo_cancelamento: string | null
  created_at: string
  decidido_em: string | null
  documentos: DocumentoRead[]
  proximos_status: StatusMatricula[]
  serie_label: string
  documentos_pendentes: number
}

export interface ResponsavelPreMatriculaInput {
  nome: string
  cpf: string
  email?: string | null
  telefone?: string | null
  parentesco: Parentesco
  responsavel_financeiro?: boolean
  pode_buscar?: boolean
}

export interface AlunoDadosInput {
  nome: string
  data_nascimento: string
  cpf?: string | null
}

export interface PreMatriculaCreateInput {
  aluno_id?: number | null
  aluno?: AlunoDadosInput | null
  responsaveis?: ResponsavelPreMatriculaInput[]
  ano_letivo: number
  serie: Serie
  turno: Turno
  tamanho_farda?: string | null
  observacoes?: string | null
}
