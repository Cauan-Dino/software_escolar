// Tipos espelhando 1:1 os schemas Pydantic do backend (snake_case, sem conversão).

export type Role = 'ADMIN' | 'SECRETARIA' | 'FINANCEIRO' | 'PROFESSOR' | 'RESPONSAVEL'

export interface Page<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

// --- auth ------------------------------------------------------------------

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

export interface UserCreate {
  email: string
  nome: string
  password: string
  role: Role
}

export interface UserUpdate {
  nome?: string
  role?: Role
  is_active?: boolean
}

// --- pessoas: alunos ---------------------------------------------------------

export type Parentesco = 'MAE' | 'PAI' | 'AVO' | 'TIO' | 'OUTRO'

export interface VinculoCreate {
  responsavel_id: number
  parentesco: Parentesco
  responsavel_financeiro: boolean
  pode_buscar: boolean
}

export interface VinculoRead {
  responsavel_id: number
  nome: string
  parentesco: Parentesco
  responsavel_financeiro: boolean
  pode_buscar: boolean
}

export interface AlunoCreate {
  nome: string
  data_nascimento: string
  cpf?: string | null
  responsaveis: VinculoCreate[]
}

export interface AlunoUpdate {
  nome?: string
  data_nascimento?: string
  cpf?: string | null
}

export interface AlunoRead {
  id: number
  nome: string
  data_nascimento: string
  cpf: string | null
  responsaveis: VinculoRead[]
}

export interface AlunoListItem {
  id: number
  nome: string
  data_nascimento: string
  cpf: string | null
}

// --- pessoas: responsáveis -----------------------------------------------

export interface AcessoCreate {
  email: string
  password: string
}

export interface ResponsavelCreate {
  nome: string
  cpf: string
  email?: string | null
  telefone?: string | null
  acesso?: AcessoCreate | null
}

export interface ResponsavelUpdate {
  nome?: string
  email?: string | null
  telefone?: string | null
}

export interface ResponsavelRead {
  id: number
  user_id: number | null
  nome: string
  cpf: string
  email: string | null
  telefone: string | null
}

export interface ResponsavelListItem {
  id: number
  user_id: number | null
  nome: string
  cpf: string
  email: string | null
  telefone: string | null
  tem_acesso: boolean
}

// --- pessoas: professores --------------------------------------------------

export interface ProfessorCreate {
  nome: string
  cpf: string
  email?: string | null
  telefone?: string | null
  formacao?: string | null
  acesso?: AcessoCreate | null
}

export interface ProfessorUpdate {
  nome?: string
  email?: string | null
  telefone?: string | null
  formacao?: string | null
}

export interface ProfessorRead {
  id: number
  user_id: number | null
  nome: string
  cpf: string
  email: string | null
  telefone: string | null
  formacao: string | null
}

export interface ProfessorListItem {
  id: number
  user_id: number | null
  nome: string
  cpf: string
  email: string | null
  formacao: string | null
}

// --- pessoas: funcionários --------------------------------------------------

export type TipoFuncionario = 'ADMINISTRATIVO' | 'PRESTADOR_SERVICO'

export interface FuncionarioAcesso extends AcessoCreate {
  role: 'ADMIN' | 'SECRETARIA' | 'FINANCEIRO'
}

export interface FuncionarioCreate {
  nome: string
  cpf: string
  email?: string | null
  telefone?: string | null
  cargo: string
  tipo: TipoFuncionario
  acesso?: FuncionarioAcesso | null
}

export interface FuncionarioUpdate {
  nome?: string
  email?: string | null
  telefone?: string | null
  cargo?: string
  tipo?: TipoFuncionario
}

export interface FuncionarioRead {
  id: number
  user_id: number | null
  nome: string
  cpf: string
  email: string | null
  telefone: string | null
  cargo: string
  tipo: TipoFuncionario
}

export interface FuncionarioListItem {
  id: number
  user_id: number | null
  nome: string
  cpf: string
  cargo: string
  tipo: TipoFuncionario
}

// --- turmas ------------------------------------------------------------------

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

export const SERIE_LABELS: Record<Serie, string> = {
  MATERNAL_1: 'Maternal 1',
  MATERNAL_2: 'Maternal 2',
  INFANTIL_1: 'Infantil 1',
  INFANTIL_2: 'Infantil 2',
  ANO_1: '1º ano',
  ANO_2: '2º ano',
  ANO_3: '3º ano',
  ANO_4: '4º ano',
  ANO_5: '5º ano',
}

export const TURNO_LABELS: Record<Turno, string> = {
  MANHA: 'Manhã',
  TARDE: 'Tarde',
  INTEGRAL: 'Integral',
}

export interface TurmaCreate {
  serie: Serie
  ano_letivo: number
  turno: Turno
  capacidade: number
}

export interface TurmaUpdate {
  capacidade?: number
  ativa?: boolean
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

// --- matrícula ---------------------------------------------------------------

export type StatusMatricula =
  | 'PRE_MATRICULA'
  | 'EM_ANALISE'
  | 'APROVADA'
  | 'AGUARDANDO_PAGAMENTO'
  | 'ATIVA'
  | 'REJEITADA'
  | 'CANCELADA'

export type TipoMatricula = 'NOVA' | 'REMATRICULA'

export type TipoDocumento =
  | 'CERTIDAO_NASCIMENTO'
  | 'CARTAO_VACINA'
  | 'COMPROVANTE_RESIDENCIA'
  | 'DOCUMENTO_RESPONSAVEL'

export const STATUS_MATRICULA_LABELS: Record<StatusMatricula, string> = {
  PRE_MATRICULA: 'Pré-matrícula',
  EM_ANALISE: 'Em análise',
  APROVADA: 'Aprovada',
  AGUARDANDO_PAGAMENTO: 'Aguardando pagamento',
  ATIVA: 'Ativa',
  REJEITADA: 'Rejeitada',
  CANCELADA: 'Cancelada',
}

export const DOCUMENTO_LABELS: Record<TipoDocumento, string> = {
  CERTIDAO_NASCIMENTO: 'Certidão de nascimento',
  CARTAO_VACINA: 'Cartão de vacina',
  COMPROVANTE_RESIDENCIA: 'Comprovante de residência',
  DOCUMENTO_RESPONSAVEL: 'Documento do responsável',
}

export interface ResponsavelPreMatricula {
  nome: string
  cpf: string
  email?: string | null
  telefone?: string | null
  parentesco: Parentesco
  responsavel_financeiro: boolean
  pode_buscar: boolean
}

export interface PreMatriculaCreate {
  aluno_id?: number | null
  aluno?: { nome: string; data_nascimento: string; cpf?: string | null } | null
  responsaveis: ResponsavelPreMatricula[]
  ano_letivo: number
  serie: Serie
  turno: Turno
  tamanho_farda?: string | null
  observacoes?: string | null
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
  tipo: TipoMatricula
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
