import { api } from './client'
import type { AlunoChamada, RegistroFrequenciaInput } from '../types/api'

export const frequenciaApi = {
  chamadaDoDia: (turmaId: number, data: string) =>
    api
      .get<AlunoChamada[]>(`/frequencia/turmas/${turmaId}`, { params: { data } })
      .then((r) => r.data),

  lancarChamada: (turmaId: number, data: string, registros: RegistroFrequenciaInput[]) =>
    api
      .post(`/frequencia/turmas/${turmaId}`, { registros }, { params: { data } })
      .then((r) => r.data),
}
