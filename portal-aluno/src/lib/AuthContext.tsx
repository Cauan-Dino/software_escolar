import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { authApi } from '../api/auth'
import { alunoApi } from '../api/aluno'
import { getAccessToken, setAccessToken } from '../api/client'
import type { AlunoRead, UserRead } from '../types/api'

interface AuthContextValue {
  usuario: UserRead | null
  aluno: AlunoRead | null
  carregando: boolean
  login: (email: string, senha: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<UserRead | null>(null)
  const [aluno, setAluno] = useState<AlunoRead | null>(null)
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    async function bootstrap() {
      if (!getAccessToken()) {
        setCarregando(false)
        return
      }
      try {
        const me = await authApi.me()
        setUsuario(me)
        const eu = await alunoApi.eu()
        setAluno(eu)
      } catch {
        setAccessToken(null)
      } finally {
        setCarregando(false)
      }
    }
    bootstrap()
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      usuario,
      aluno,
      carregando,
      login: async (email: string, senha: string) => {
        const tokens = await authApi.login(email, senha)
        setAccessToken(tokens.access_token)
        setUsuario(tokens.user)
        const eu = await alunoApi.eu()
        setAluno(eu)
      },
      logout: () => {
        authApi.logout().catch(() => {})
        setAccessToken(null)
        setUsuario(null)
        setAluno(null)
      },
    }),
    [usuario, aluno, carregando],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de AuthProvider')
  return ctx
}
