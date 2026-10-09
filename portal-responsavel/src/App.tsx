import { Navigate, Route, Routes } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { AuthProvider, useAuth } from './lib/AuthContext'
import { FilhoProvider } from './lib/FilhoContext'
import { AppLayout } from './layout/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { BoletimPage } from './pages/BoletimPage'
import { FrequenciaPage } from './pages/FrequenciaPage'
import { FinanceiroPage } from './pages/FinanceiroPage'
import { MatriculaPage } from './pages/MatriculaPage'
import { ComunicacaoPage } from './pages/ComunicacaoPage'
import { CalendarioPage } from './pages/CalendarioPage'
import { PerfilPage } from './pages/PerfilPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { usuario, carregando } = useAuth()
  if (carregando) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-slate-400">
        <Loader2 className="animate-spin" size={20} />
      </div>
    )
  }
  if (!usuario) return <Navigate to="/login" replace />
  return <FilhoProvider>{children}</FilhoProvider>
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
        <Route index element={<DashboardPage />} />
        <Route path="boletim" element={<BoletimPage />} />
        <Route path="frequencia" element={<FrequenciaPage />} />
        <Route path="financeiro" element={<FinanceiroPage />} />
        <Route path="matricula" element={<MatriculaPage />} />
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
