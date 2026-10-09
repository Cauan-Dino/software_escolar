import { api } from './client'
import type {
  EventoCalendarioCreate,
  EventoCalendarioRead,
  EventoCalendarioUpdate,
} from '../types/calendario'

export const calendarioApi = {
  listarEventos: (de?: string, ate?: string, turmaId?: number) =>
    api
      .get<EventoCalendarioRead[]>('/calendario/eventos', {
        params: { de, ate, turma_id: turmaId },
      })
      .then((r) => r.data),

  criarEvento: (dados: EventoCalendarioCreate) =>
    api.post<EventoCalendarioRead>('/calendario/eventos', dados).then((r) => r.data),

  editarEvento: (id: number, dados: EventoCalendarioUpdate) =>
    api.patch<EventoCalendarioRead>(`/calendario/eventos/${id}`, dados).then((r) => r.data),

  removerEvento: (id: number) => api.delete(`/calendario/eventos/${id}`).then(() => undefined),
}
