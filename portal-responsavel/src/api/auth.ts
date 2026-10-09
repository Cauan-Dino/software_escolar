import { api } from './client'
import type { TokenResponse, UserRead } from '../types/api'

export const authApi = {
  login: (email: string, password: string) =>
    api.post<TokenResponse>('/auth/login', { email, password }).then((r) => r.data),
  logout: () => api.post('/auth/logout'),
  me: () => api.get<UserRead>('/auth/me').then((r) => r.data),
  changePassword: (current_password: string, new_password: string) =>
    api.post('/auth/me/senha', { current_password, new_password }),
}
