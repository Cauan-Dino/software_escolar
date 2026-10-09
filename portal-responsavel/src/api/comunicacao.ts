import { api } from './client'
import type { AvisoRead, Page } from '../types/api'

export const comunicacaoApi = {
  listarAvisos: (params?: { limit?: number; offset?: number }) =>
    api.get<Page<AvisoRead>>('/comunicacao/avisos', { params }).then((r) => r.data),
  marcarLido: (id: number) => api.post(`/comunicacao/avisos/${id}/lido`),
}
