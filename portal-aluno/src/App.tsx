import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/AuthContext'
import { AppLayout } from './layout/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { BoletimPage } from './pages/BoletimPage'
import { FrequenciaPage } from './pages/FrequenciaPage'
import { FinanceiroPage } from './pages/FinanceiroPage'
import { CalendarioPage } from './pages/CalendarioPage'
import { AvisosPage } from './pages/AvisosPage'
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
        <Route index element={<HomePage />} />
        <Route path="boletim" element={<BoletimPage />} />
        <Route path="frequencia" element={<FrequenciaPage />} />
        <Route path="financeiro" element={<FinanceiroPage />} />
        <Route path="calendario" element={<CalendarioPage />} />
        <Route path="avisos" element={<AvisosPage />} />
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
