import { api } from './client'
import type { Serie, TurmaCreate, TurmaRead, TurmaUpdate } from '../types/api'

export const turmasApi = {
  list: (params?: { ano_letivo?: number; serie?: Serie; ativa?: boolean }) =>
    api.get<TurmaRead[]>('/turmas', { params }).then((r) => r.data),

  minhas: () => api.get<TurmaRead[]>('/turmas/minhas').then((r) => r.data),

  get: (id: number) => api.get<TurmaRead>(`/turmas/${id}`).then((r) => r.data),

  create: (payload: TurmaCreate) =>
    api.post<TurmaRead>('/turmas', payload).then((r) => r.data),

  update: (id: number, payload: TurmaUpdate) =>
    api.patch<TurmaRead>(`/turmas/${id}`, payload).then((r) => r.data),

  addProfessor: (turmaId: number, professorId: number) =>
    api
      .post<TurmaRead>(`/turmas/${turmaId}/professores`, { professor_id: professorId })
      .then((r) => r.data),

  removeProfessor: (turmaId: number, professorId: number) =>
    api.delete<TurmaRead>(`/turmas/${turmaId}/professores/${professorId}`).then((r) => r.data),
}
