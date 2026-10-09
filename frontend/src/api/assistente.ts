import { api } from './client'
import type { ConversaDetalhe, ConversaRead, DecisaoAcao, RespostaChat } from '../types/assistente'

export const assistenteApi = {
  criarConversa: () => api.post<ConversaRead>('/assistente/conversas').then((r) => r.data),

  buscarConversa: (id: number) =>
    api.get<ConversaDetalhe>(`/assistente/conversas/${id}`).then((r) => r.data),

  enviarMensagem: (conversaId: number, texto: string) =>
    api
      .post<RespostaChat>(`/assistente/conversas/${conversaId}/mensagens`, { texto })
      .then((r) => r.data),

  confirmarAcao: (acaoId: string) =>
    api.post<DecisaoAcao>(`/assistente/acoes/${acaoId}/confirmar`).then((r) => r.data),

  cancelarAcao: (acaoId: string) =>
    api.post<DecisaoAcao>(`/assistente/acoes/${acaoId}/cancelar`).then((r) => r.data),
}
