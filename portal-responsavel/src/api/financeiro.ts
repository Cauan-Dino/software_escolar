import { api } from './client'
import type { CobrancaRead, Page } from '../types/api'

export const financeiroApi = {
  cobrancas: (alunoId?: number) =>
    api
      .get<Page<CobrancaRead>>('/financeiro/cobrancas', {
        params: { aluno_id: alunoId, limit: 100 },
      })
      .then((r) => r.data),
}
