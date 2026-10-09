import { api } from './client'
import type {
  AlunoChamada,
  CorrigirRegistro,
  FrequenciaRead,
  HistoricoFrequencia,
  RegistroFrequenciaInput,
} from '../types/frequencia'

export const frequenciaApi = {
  listarChamadaDoDia: (turmaId: number, data: string) =>
    api
      .get<AlunoChamada[]>(`/frequencia/turmas/${turmaId}`, { params: { data } })
      .then((r) => r.data),

  lancarChamada: (turmaId: number, data: string, registros: RegistroFrequenciaInput[]) =>
    api
      .post<FrequenciaRead[]>(
        `/frequencia/turmas/${turmaId}`,
        { registros },
        { params: { data } },
      )
      .then((r) => r.data),

  corrigirRegistro: (
    turmaId: number,
    alunoId: number,
    data: string,
    dados: CorrigirRegistro,
  ) =>
    api
      .patch<FrequenciaRead>(`/frequencia/turmas/${turmaId}/alunos/${alunoId}`, dados, {
        params: { data },
      })
      .then((r) => r.data),

  historicoDoAluno: (alunoId: number, de: string, ate: string) =>
    api
      .get<HistoricoFrequencia>(`/frequencia/alunos/${alunoId}`, { params: { de, ate } })
      .then((r) => r.data),
}
