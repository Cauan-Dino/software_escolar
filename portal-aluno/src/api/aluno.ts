import { api } from './client'
import type {
  AlunoRead,
  AvisoRead,
  BoletimRead,
  CobrancaRead,
  EventoCalendarioRead,
  HistoricoFrequencia,
  Page,
} from '../types/api'

export const alunoApi = {
  eu: () => api.get<AlunoRead>('/pessoas/alunos/eu').then((r) => r.data),

  boletim: (alunoId: number) =>
    api.get<BoletimRead>(`/notas/alunos/${alunoId}/boletim`).then((r) => r.data),

  frequencia: (alunoId: number, de: string, ate: string) =>
    api
      .get<HistoricoFrequencia>(`/frequencia/alunos/${alunoId}`, { params: { de, ate } })
      .then((r) => r.data),

  cobrancas: (alunoId: number) =>
    api
      .get<Page<CobrancaRead>>('/financeiro/cobrancas', { params: { aluno_id: alunoId } })
      .then((r) => r.data),

  eventos: (de: string, ate: string) =>
    api.get<EventoCalendarioRead[]>('/calendario/eventos', { params: { de, ate } }).then((r) => r.data),

  avisos: () => api.get<Page<AvisoRead>>('/comunicacao/avisos').then((r) => r.data),

  marcarAvisoLido: (avisoId: number) => api.post(`/comunicacao/avisos/${avisoId}/lido`),
}
