export type Periodo = 'BIMESTRE_1' | 'BIMESTRE_2' | 'BIMESTRE_3' | 'BIMESTRE_4'

export const PERIODO_LABELS: Record<Periodo, string> = {
  BIMESTRE_1: '1º Bimestre',
  BIMESTRE_2: '2º Bimestre',
  BIMESTRE_3: '3º Bimestre',
  BIMESTRE_4: '4º Bimestre',
}

export const PERIODOS: Periodo[] = ['BIMESTRE_1', 'BIMESTRE_2', 'BIMESTRE_3', 'BIMESTRE_4']

export interface NotaUpsert {
  disciplina: string
  periodo: Periodo
  valor: number
  observacao?: string | null
}

export interface NotaRead {
  id: number
  aluno_id: number
  turma_id: number
  disciplina: string
  periodo: Periodo
  valor: number
  observacao: string | null
  lancado_por_user_id: number
  lancado_em: string
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

export interface NotaPeriodo {
  periodo: Periodo
  valor: number
  observacao: string | null
}

export type Situacao = 'APROVADO' | 'RECUPERACAO' | 'REPROVADO' | 'SEM_NOTA'

export const SITUACAO_LABELS: Record<Situacao, string> = {
  APROVADO: 'Aprovado',
  RECUPERACAO: 'Recuperação',
  REPROVADO: 'Reprovado',
  SEM_NOTA: 'Sem nota',
}

export interface BoletimDisciplina {
  disciplina: string
  notas: NotaPeriodo[]
  media: number | null
  situacao: Situacao
}

export interface BoletimRead {
  aluno_id: number
  disciplinas: BoletimDisciplina[]
}
