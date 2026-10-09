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

export interface LancarChamada {
  registros: RegistroFrequenciaInput[]
}

export interface CorrigirRegistro {
  status: StatusFrequencia
  observacao?: string | null
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
