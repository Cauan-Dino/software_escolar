export type PublicoAlvo = 'TODOS' | 'TURMA' | 'RESPONSAVEIS' | 'PROFESSORES'

export const PUBLICO_ALVO_LABELS: Record<PublicoAlvo, string> = {
  TODOS: 'Todos',
  TURMA: 'Turma',
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

export interface AvisoCreate {
  titulo: string
  corpo: string
  publico_alvo: PublicoAlvo
  turma_id?: number | null
  fixado?: boolean
}

export interface AvisoUpdate {
  titulo?: string
  corpo?: string
  publico_alvo?: PublicoAlvo
  turma_id?: number | null
  fixado?: boolean
}

export interface NaoLidosTotal {
  total: number
}
