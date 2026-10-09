import { api } from './client'
import type { HistoricoFrequencia } from '../types/api'

export const frequenciaApi = {
  historico: (alunoId: number, de: string, ate: string) =>
    api
      .get<HistoricoFrequencia>(`/frequencia/alunos/${alunoId}`, { params: { de, ate } })
      .then((r) => r.data),
}
