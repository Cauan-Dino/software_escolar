import { api } from './client'
import type { EventoCalendarioCreate, EventoCalendarioRead } from '../types/api'

export const calendarioApi = {
  listarEventos: (de?: string, ate?: string) =>
    api
      .get<EventoCalendarioRead[]>('/calendario/eventos', { params: { de, ate } })
      .then((r) => r.data),

  criarEvento: (dados: EventoCalendarioCreate) =>
    api.post<EventoCalendarioRead>('/calendario/eventos', dados).then((r) => r.data),
}
