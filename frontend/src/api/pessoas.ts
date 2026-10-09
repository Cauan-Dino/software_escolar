import { api } from './client'
import type {
  AlunoCreate,
  AlunoListItem,
  AlunoRead,
  AlunoUpdate,
  FuncionarioCreate,
  FuncionarioListItem,
  FuncionarioRead,
  FuncionarioUpdate,
  Page,
  ProfessorCreate,
  ProfessorListItem,
  ProfessorRead,
  ProfessorUpdate,
  ResponsavelCreate,
  ResponsavelListItem,
  ResponsavelRead,
  ResponsavelUpdate,
  VinculoCreate,
} from '../types/api'

const PREFIX = '/pessoas'

export const alunosApi = {
  list: (params?: { limit?: number; offset?: number; busca?: string }) =>
    api.get<Page<AlunoListItem>>(`${PREFIX}/alunos`, { params }).then((r) => r.data),

  get: (id: number) => api.get<AlunoRead>(`${PREFIX}/alunos/${id}`).then((r) => r.data),

  create: (payload: AlunoCreate) =>
    api.post<AlunoRead>(`${PREFIX}/alunos`, payload).then((r) => r.data),

  update: (id: number, payload: AlunoUpdate) =>
    api.patch<AlunoRead>(`${PREFIX}/alunos/${id}`, payload).then((r) => r.data),

  remove: (id: number) => api.delete(`${PREFIX}/alunos/${id}`),

  addVinculo: (alunoId: number, payload: VinculoCreate) =>
    api.post<AlunoRead>(`${PREFIX}/alunos/${alunoId}/responsaveis`, payload).then((r) => r.data),
}

export const responsaveisApi = {
  list: (params?: { limit?: number; offset?: number; busca?: string }) =>
    api.get<Page<ResponsavelListItem>>(`${PREFIX}/responsaveis`, { params }).then((r) => r.data),

  get: (id: number) =>
    api.get<ResponsavelRead>(`${PREFIX}/responsaveis/${id}`).then((r) => r.data),

  create: (payload: ResponsavelCreate) =>
    api.post<ResponsavelRead>(`${PREFIX}/responsaveis`, payload).then((r) => r.data),

  update: (id: number, payload: ResponsavelUpdate) =>
    api.patch<ResponsavelRead>(`${PREFIX}/responsaveis/${id}`, payload).then((r) => r.data),

  grantAcesso: (id: number, email: string, password: string) =>
    api
      .post<ResponsavelRead>(`${PREFIX}/responsaveis/${id}/acesso`, { email, password })
      .then((r) => r.data),
}

export const professoresApi = {
  list: (params?: { limit?: number; offset?: number; busca?: string }) =>
    api.get<Page<ProfessorListItem>>(`${PREFIX}/professores`, { params }).then((r) => r.data),

  get: (id: number) => api.get<ProfessorRead>(`${PREFIX}/professores/${id}`).then((r) => r.data),

  create: (payload: ProfessorCreate) =>
    api.post<ProfessorRead>(`${PREFIX}/professores`, payload).then((r) => r.data),

  update: (id: number, payload: ProfessorUpdate) =>
    api.patch<ProfessorRead>(`${PREFIX}/professores/${id}`, payload).then((r) => r.data),

  remove: (id: number) => api.delete(`${PREFIX}/professores/${id}`),
}

export const funcionariosApi = {
  list: (params?: { limit?: number; offset?: number; busca?: string }) =>
    api.get<Page<FuncionarioListItem>>(`${PREFIX}/funcionarios`, { params }).then((r) => r.data),

  get: (id: number) =>
    api.get<FuncionarioRead>(`${PREFIX}/funcionarios/${id}`).then((r) => r.data),

  create: (payload: FuncionarioCreate) =>
    api.post<FuncionarioRead>(`${PREFIX}/funcionarios`, payload).then((r) => r.data),

  update: (id: number, payload: FuncionarioUpdate) =>
    api.patch<FuncionarioRead>(`${PREFIX}/funcionarios/${id}`, payload).then((r) => r.data),

  remove: (id: number) => api.delete(`${PREFIX}/funcionarios/${id}`),
}
