import { api } from './client'
import type {
  MatriculaRead,
  Page,
  PreMatriculaCreate,
  Serie,
  StatusMatricula,
  TipoDocumento,
} from '../types/api'

export const matriculasApi = {
  list: (params?: {
    limit?: number
    offset?: number
    status?: StatusMatricula
    ano_letivo?: number
    serie?: Serie
  }) => api.get<Page<MatriculaRead>>('/matriculas', { params }).then((r) => r.data),

  get: (id: number) => api.get<MatriculaRead>(`/matriculas/${id}`).then((r) => r.data),

  create: (payload: PreMatriculaCreate) =>
    api.post<MatriculaRead>('/matriculas', payload).then((r) => r.data),

  iniciarAnalise: (id: number) =>
    api.post<MatriculaRead>(`/matriculas/${id}/analise`).then((r) => r.data),

  aprovar: (id: number, turmaId: number) =>
    api.post<MatriculaRead>(`/matriculas/${id}/aprovar`, { turma_id: turmaId }).then((r) => r.data),

  rejeitar: (id: number, motivo: string) =>
    api.post<MatriculaRead>(`/matriculas/${id}/rejeitar`, { motivo }).then((r) => r.data),

  cancelar: (id: number, motivo: string) =>
    api.post<MatriculaRead>(`/matriculas/${id}/cancelar`, { motivo }).then((r) => r.data),

  checarDocumento: (id: number, tipo: TipoDocumento, entregue: boolean) =>
    api
      .patch<MatriculaRead>(`/matriculas/${id}/documentos/${tipo}`, { entregue })
      .then((r) => r.data),

  uploadDocumento: (id: number, tipo: TipoDocumento, arquivo: File) => {
    const form = new FormData()
    form.append('arquivo', arquivo)
    return api
      .post<MatriculaRead>(`/matriculas/${id}/documentos/${tipo}/arquivo`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },

  downloadDocumentoUrl: (id: number, tipo: TipoDocumento) =>
    `${api.defaults.baseURL}/matriculas/${id}/documentos/${tipo}/arquivo`,
}
