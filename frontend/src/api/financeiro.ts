import { api } from './client'
import type { Page } from '../types/api'
import type {
  BolsaCreate,
  BolsaRead,
  CobrancaCreate,
  CobrancaRead,
  StatusCobranca,
  TabelaPrecoCreate,
  TabelaPrecoRead,
} from '../types/financeiro'

export function listarCobrancas(params?: {
  limit?: number
  offset?: number
  aluno_id?: number
  status?: StatusCobranca
}) {
  return api.get<Page<CobrancaRead>>('/financeiro/cobrancas', { params }).then((r) => r.data)
}

export function criarCobranca(dados: CobrancaCreate) {
  return api.post<CobrancaRead>('/financeiro/cobrancas', dados).then((r) => r.data)
}

export function gerarMensalidades(competencia: string) {
  return api
    .post<CobrancaRead[]>('/financeiro/cobrancas/gerar-mensalidades', null, {
      params: { competencia },
    })
    .then((r) => r.data)
}

export function marcarPaga(id: number) {
  return api.post<CobrancaRead>(`/financeiro/cobrancas/${id}/marcar-paga`).then((r) => r.data)
}

export function listarBolsas(alunoId?: number) {
  return api
    .get<BolsaRead[]>('/financeiro/bolsas', { params: alunoId ? { aluno_id: alunoId } : undefined })
    .then((r) => r.data)
}

export function criarBolsa(dados: BolsaCreate) {
  return api.post<BolsaRead>('/financeiro/bolsas', dados).then((r) => r.data)
}

export function listarPrecos() {
  return api.get<TabelaPrecoRead[]>('/financeiro/precos').then((r) => r.data)
}

export function salvarPreco(dados: TabelaPrecoCreate) {
  return api.post<TabelaPrecoRead>('/financeiro/precos', dados).then((r) => r.data)
}
