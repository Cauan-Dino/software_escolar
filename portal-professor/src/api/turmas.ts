import { api } from './client'
import type { TurmaRead } from '../types/api'

export const turmasApi = {
  minhas: () => api.get<TurmaRead[]>('/turmas/minhas').then((r) => r.data),
}
