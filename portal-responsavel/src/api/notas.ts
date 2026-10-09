import { api } from './client'
import type { BoletimRead } from '../types/api'

export const notasApi = {
  boletim: (alunoId: number) =>
    api.get<BoletimRead>(`/notas/alunos/${alunoId}/boletim`).then((r) => r.data),
}
