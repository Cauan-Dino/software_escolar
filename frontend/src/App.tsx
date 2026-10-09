import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/AuthContext'
import { AppLayout } from './layout/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { AlunosPage } from './pages/AlunosPage'
import { TurmasPage } from './pages/TurmasPage'
import { MatriculasPage } from './pages/MatriculasPage'
import { ResponsaveisPage } from './pages/ResponsaveisPage'
import { ProfessoresPage } from './pages/ProfessoresPage'
import { FuncionariosPage } from './pages/FuncionariosPage'
import { UsuariosPage } from './pages/UsuariosPage'
import { PerfilPage } from './pages/PerfilPage'
import { NotasPage } from './pages/NotasPage'
import { FrequenciaPage } from './pages/FrequenciaPage'
import { CalendarioPage } from './pages/CalendarioPage'
import { ComunicacaoPage } from './pages/ComunicacaoPage'
import { FinanceiroPage } from './pages/FinanceiroPage'

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
        <Route index element={<DashboardPage />} />
        <Route path="alunos" element={<AlunosPage />} />
        <Route path="responsaveis" element={<ResponsaveisPage />} />
        <Route path="professores" element={<ProfessoresPage />} />
        <Route path="funcionarios" element={<FuncionariosPage />} />
        <Route path="turmas" element={<TurmasPage />} />
        <Route path="matriculas" element={<MatriculasPage />} />
        <Route path="notas" element={<NotasPage />} />
        <Route path="frequencia" element={<FrequenciaPage />} />
        <Route path="calendario" element={<CalendarioPage />} />
        <Route path="comunicacao" element={<ComunicacaoPage />} />
        <Route path="financeiro" element={<FinanceiroPage />} />
        <Route path="usuarios" element={<UsuariosPage />} />
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
