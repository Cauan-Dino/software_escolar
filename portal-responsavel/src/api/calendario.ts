import { api } from './client'
import type { EventoCalendarioRead } from '../types/api'

export const calendarioApi = {
  listarEventos: (de?: string, ate?: string) =>
    api
      .get<EventoCalendarioRead[]>('/calendario/eventos', { params: { de, ate } })
      .then((r) => r.data),
}
