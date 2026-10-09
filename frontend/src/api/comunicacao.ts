import { api } from './client'
import type { Page } from '../types/api'
import type { AvisoCreate, AvisoRead, AvisoUpdate, NaoLidosTotal } from '../types/comunicacao'

export const comunicacaoApi = {
  listarAvisos: (params?: { limit?: number; offset?: number }) =>
    api.get<Page<AvisoRead>>('/comunicacao/avisos', { params }).then((r) => r.data),

  contarNaoLidos: () =>
    api.get<NaoLidosTotal>('/comunicacao/avisos/nao-lidos/total').then((r) => r.data),

  criarAviso: (dados: AvisoCreate) =>
    api.post<AvisoRead>('/comunicacao/avisos', dados).then((r) => r.data),

  editarAviso: (id: number, dados: AvisoUpdate) =>
    api.patch<AvisoRead>(`/comunicacao/avisos/${id}`, dados).then((r) => r.data),

  removerAviso: (id: number) => api.delete(`/comunicacao/avisos/${id}`).then(() => undefined),

  marcarLido: (id: number) =>
    api.post(`/comunicacao/avisos/${id}/lido`).then(() => undefined),
}
