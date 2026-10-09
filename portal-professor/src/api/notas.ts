import { api } from './client'
import type { NotaUpsert, Periodo, TurmaGradeRead } from '../types/api'

export const notasApi = {
  listarGrade: (turmaId: number, periodo: Periodo) =>
    api
      .get<TurmaGradeRead>(`/notas/turmas/${turmaId}`, { params: { periodo } })
      .then((r) => r.data),

  lancarNota: (turmaId: number, alunoId: number, dados: NotaUpsert) =>
    api.put(`/notas/turmas/${turmaId}/alunos/${alunoId}`, dados).then((r) => r.data),

  listarDisciplinas: () => api.get<string[]>('/notas/disciplinas').then((r) => r.data),
}
