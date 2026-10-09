import { useEffect, useState } from 'react'
import { Loader2, CalendarDays, Megaphone, Wallet, GraduationCap, ClipboardList } from 'lucide-react'
import { calendarioApi } from '../api/calendario'
import { comunicacaoApi } from '../api/comunicacao'
import { financeiroApi } from '../api/financeiro'
import { notasApi } from '../api/notas'
import { matriculasApi } from '../api/matriculas'
import { useFilho } from '../lib/FilhoContext'
import type { AvisoRead, BoletimRead, CobrancaRead, EventoCalendarioRead, MatriculaRead } from '../types/api'
import { STATUS_MATRICULA_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'

export function DashboardPage() {
  const { filhoAtivo } = useFilho()
  const [loading, setLoading] = useState(true)
  const [eventos, setEventos] = useState<EventoCalendarioRead[]>([])
  const [avisos, setAvisos] = useState<AvisoRead[]>([])
  const [cobrancas, setCobrancas] = useState<CobrancaRead[]>([])
  const [boletim, setBoletim] = useState<BoletimRead | null>(null)
  const [matricula, setMatricula] = useState<MatriculaRead | null>(null)

  useEffect(() => {
    if (!filhoAtivo) return
    setLoading(true)
    Promise.all([
      calendarioApi.listarEventos().catch(() => []),
      comunicacaoApi.listarAvisos({ limit: 5 }).catch(() => ({ items: [] as AvisoRead[] })),
      financeiroApi.cobrancas(filhoAtivo.id).catch(() => ({ items: [] as CobrancaRead[] })),
      notasApi.boletim(filhoAtivo.id).catch(() => null),
      matriculasApi.listar({ limit: 100 }).catch(() => ({ items: [] as MatriculaRead[] })),
    ]).then(([ev, av, cob, bol, mats]) => {
      setEventos(ev.slice(0, 5))
      setAvisos(av.items)
      setCobrancas(cob.items)
      setBoletim(bol)
      const doFilho = mats.items.filter((m) => m.aluno_id === filhoAtivo.id)
      setMatricula(doFilho[0] ?? null)
      setLoading(false)
    })
  }, [filhoAtivo])

  if (!filhoAtivo) return <p className="text-slate-500">Selecione um filho.</p>

  if (loading) {
    return (
      <div className="flex justify-center py-16 text-slate-400">
        <Loader2 className="animate-spin" size={24} />
      </div>
    )
  }

  const atrasadas = cobrancas.filter((c) => c.status === 'ATRASADA')
  const avisosNaoLidos = avisos.filter((a) => !a.lido)
  const medias = boletim?.disciplinas.map((d) => d.media).filter((m): m is number => m != null) ?? []
  const mediaGeral = medias.length ? medias.reduce((a, b) => a + b, 0) / medias.length : null

  return (
    <div>
      <PageHeader title={`Olá, ${filhoAtivo.nome.split(' ')[0]}`} subtitle="Resumo da família" />

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <GraduationCap size={16} />
            <span className="text-xs font-medium uppercase">Média geral</span>
          </div>
          <p className="text-2xl font-semibold text-slate-900">
            {mediaGeral != null ? mediaGeral.toFixed(1) : '-'}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <ClipboardList size={16} />
            <span className="text-xs font-medium uppercase">Matrícula</span>
          </div>
          <p className="text-sm font-semibold text-slate-900">
            {matricula ? STATUS_MATRICULA_LABELS[matricula.status] : 'Sem registro'}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <Wallet size={16} />
            <span className="text-xs font-medium uppercase">Cobranças atrasadas</span>
          </div>
          <p className={`text-2xl font-semibold ${atrasadas.length ? 'text-red-600' : 'text-slate-900'}`}>
            {atrasadas.length}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <Megaphone size={16} />
            <span className="text-xs font-medium uppercase">Avisos não lidos</span>
          </div>
          <p className="text-2xl font-semibold text-slate-900">{avisosNaoLidos.length}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="mb-3 flex items-center gap-2">
            <CalendarDays size={16} className="text-slate-400" />
            <h2 className="text-sm font-semibold text-slate-900">Próximos eventos</h2>
          </div>
          <div className="space-y-2">
            {eventos.map((ev) => (
              <div key={ev.id} className="flex items-center justify-between text-sm">
                <span className="text-slate-700">{ev.titulo}</span>
                <span className="text-xs text-slate-400">
                  {new Date(ev.data_inicio + 'T00:00').toLocaleDateString('pt-BR')}
                </span>
              </div>
            ))}
            {eventos.length === 0 && <p className="text-sm text-slate-400">Nenhum evento próximo.</p>}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="mb-3 flex items-center gap-2">
            <Megaphone size={16} className="text-slate-400" />
            <h2 className="text-sm font-semibold text-slate-900">Avisos recentes</h2>
          </div>
          <div className="space-y-2">
            {avisos.map((a) => (
              <div key={a.id} className="text-sm">
                <p className="font-medium text-slate-800">{a.titulo}</p>
                <p className="truncate text-xs text-slate-400">{a.corpo}</p>
              </div>
            ))}
            {avisos.length === 0 && <p className="text-sm text-slate-400">Nenhum aviso publicado.</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
