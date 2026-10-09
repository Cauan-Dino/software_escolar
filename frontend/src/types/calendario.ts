// Tipos espelhando 1:1 os schemas Pydantic do módulo calendario (snake_case, sem conversão).

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

export interface EventoCalendarioCreate {
  titulo: string
  descricao?: string | null
  data_inicio: string
  data_fim?: string | null
  tipo: TipoEvento
  turma_id?: number | null
}

export interface EventoCalendarioUpdate {
  titulo?: string
  descricao?: string | null
  data_inicio?: string
  data_fim?: string | null
  tipo?: TipoEvento
}
