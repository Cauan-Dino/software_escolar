import { api } from './client'
import type { BoletimRead, NotaRead, NotaUpsert, Periodo, TurmaGradeRead } from '../types/notas'

export const notasApi = {
  listarGrade: (turmaId: number, periodo: Periodo) =>
    api
      .get<TurmaGradeRead>(`/notas/turmas/${turmaId}`, { params: { periodo } })
      .then((r) => r.data),

  lancarNota: (turmaId: number, alunoId: number, dados: NotaUpsert) =>
    api
      .put<NotaRead>(`/notas/turmas/${turmaId}/alunos/${alunoId}`, dados)
      .then((r) => r.data),

  buscarBoletim: (alunoId: number) =>
    api.get<BoletimRead>(`/notas/alunos/${alunoId}/boletim`).then((r) => r.data),

  listarDisciplinas: () => api.get<string[]>('/notas/disciplinas').then((r) => r.data),
}
