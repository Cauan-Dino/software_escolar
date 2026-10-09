import { api } from './client'
import type { Page, Role, TokenResponse, UserCreate, UserRead, UserUpdate } from '../types/api'

export const authApi = {
  login: (email: string, password: string) =>
    api.post<TokenResponse>('/auth/login', { email, password }).then((r) => r.data),

  refresh: () => api.post<TokenResponse>('/auth/refresh').then((r) => r.data),

  logout: () => api.post('/auth/logout'),

  me: () => api.get<UserRead>('/auth/me').then((r) => r.data),

  changePassword: (current_password: string, new_password: string) =>
    api.post('/auth/me/senha', { current_password, new_password }),

  listUsers: (params?: { limit?: number; offset?: number; role?: Role }) =>
    api.get<Page<UserRead>>('/auth/users', { params }).then((r) => r.data),

  createUser: (payload: UserCreate) =>
    api.post<UserRead>('/auth/users', payload).then((r) => r.data),

  updateUser: (id: number, payload: UserUpdate) =>
    api.patch<UserRead>(`/auth/users/${id}`, payload).then((r) => r.data),
}
