import { api } from './client'
import type { AlunoRead } from '../types/api'

export const pessoasApi = {
  meusFilhos: () => api.get<AlunoRead[]>('/pessoas/alunos/meus').then((r) => r.data),
  getAluno: (alunoId: number) => api.get<AlunoRead>(`/pessoas/alunos/${alunoId}`).then((r) => r.data),
}
