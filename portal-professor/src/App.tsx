import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/AuthContext'
import { AppLayout } from './layout/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { MinhasTurmasPage } from './pages/MinhasTurmasPage'
import { NotasPage } from './pages/NotasPage'
import { FrequenciaPage } from './pages/FrequenciaPage'
import { ComunicacaoPage } from './pages/ComunicacaoPage'
import { CalendarioPage } from './pages/CalendarioPage'
import { PerfilPage } from './pages/PerfilPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { usuario, carregando } = useAuth()
  if (carregando) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-slate-400">
        Carregando...
      </div>
    )
  }
  if (!usuario) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <AppLayout />
          </PrivateRoute>
        }
      >
        <Route index element={<MinhasTurmasPage />} />
        <Route path="notas" element={<NotasPage />} />
        <Route path="frequencia" element={<FrequenciaPage />} />
        <Route path="comunicacao" element={<ComunicacaoPage />} />
        <Route path="calendario" element={<CalendarioPage />} />
        <Route path="perfil" element={<PerfilPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
