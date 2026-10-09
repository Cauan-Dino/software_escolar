import { api } from './client'
import type { MatriculaRead, Page, PreMatriculaCreateInput } from '../types/api'

export const matriculasApi = {
  listar: (params?: { limit?: number; offset?: number }) =>
    api.get<Page<MatriculaRead>>('/matriculas', { params }).then((r) => r.data),

  criar: (payload: PreMatriculaCreateInput) =>
    api.post<MatriculaRead>('/matriculas', payload).then((r) => r.data),

  cancelar: (matriculaId: number, motivo: string) =>
    api.post<MatriculaRead>(`/matriculas/${matriculaId}/cancelar`, { motivo }).then((r) => r.data),

  uploadDocumento: (matriculaId: number, tipo: string, arquivo: File) => {
    const form = new FormData()
    form.append('arquivo', arquivo)
    return api
      .post<MatriculaRead>(`/matriculas/${matriculaId}/documentos/${tipo}/arquivo`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },
}
