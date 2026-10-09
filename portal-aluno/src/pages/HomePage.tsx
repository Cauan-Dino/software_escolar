import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, CalendarCheck, CalendarDays, Megaphone, Loader2 } from 'lucide-react'
import { useAuth } from '../lib/AuthContext'
import { alunoApi } from '../api/aluno'
import type { AvisoRead, BoletimRead, EventoCalendarioRead, HistoricoFrequencia } from '../types/api'

function hoje(): string {
  return new Date().toISOString().slice(0, 10)
}

function inicioAno(): string {
  return `${new Date().getFullYear()}-01-01`
}

function em90Dias(): string {
  const d = new Date()
  d.setDate(d.getDate() + 90)
  return d.toISOString().slice(0, 10)
}

export function HomePage() {
  const { aluno } = useAuth()
  const [boletim, setBoletim] = useState<BoletimRead | null>(null)
  const [frequencia, setFrequencia] = useState<HistoricoFrequencia | null>(null)
  const [eventos, setEventos] = useState<EventoCalendarioRead[]>([])
  const [avisos, setAvisos] = useState<AvisoRead[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!aluno) return
    Promise.all([
      alunoApi.boletim(aluno.id).catch(() => null),
      alunoApi.frequencia(aluno.id, inicioAno(), hoje()).catch(() => null),
      alunoApi.eventos(hoje(), em90Dias()).catch(() => []),
      alunoApi.avisos().catch(() => null),
    ]).then(([b, f, ev, av]) => {
      setBoletim(b)
      setFrequencia(f)
      setEventos(ev.slice(0, 3))
      setAvisos(av?.items.filter((a) => !a.lido).slice(0, 3) ?? [])
      setLoading(false)
    })
  }, [aluno])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400">
        <Loader2 className="animate-spin" />
      </div>
    )
  }

  const mediaGeral = (() => {
    const medias = (boletim?.disciplinas ?? [])
      .map((d) => d.media)
      .filter((m): m is number => m !== null)
    if (medias.length === 0) return null
    return medias.reduce((a, b) => a + b, 0) / medias.length
  })()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">Olá, {aluno?.nome.split(' ')[0]}</h1>
        <p className="text-sm text-slate-500">Resumo da sua vida acadêmica</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Link
          to="/boletim"
          className="rounded-xl border border-slate-200 bg-white p-4 hover:border-emerald-300"
        >
          <BookOpen size={18} className="mb-2 text-emerald-600" />
          <p className="text-2xl font-semibold text-slate-900">
            {mediaGeral !== null ? mediaGeral.toFixed(1) : '—'}
          </p>
          <p className="text-xs text-slate-500">Média geral</p>
        </Link>
        <Link
          to="/frequencia"
          className="rounded-xl border border-slate-200 bg-white p-4 hover:border-emerald-300"
        >
          <CalendarCheck size={18} className="mb-2 text-emerald-600" />
          <p className="text-2xl font-semibold text-slate-900">
            {frequencia ? `${frequencia.percentual_presenca.toFixed(0)}%` : '—'}
          </p>
          <p className="text-xs text-slate-500">Frequência no ano</p>
        </Link>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-900">
            <CalendarDays size={16} className="text-emerald-600" />
            Próximos eventos
          </div>
          <Link to="/calendario" className="text-xs font-medium text-emerald-600">
            Ver tudo
          </Link>
        </div>
        {eventos.length === 0 ? (
          <p className="text-sm text-slate-400">Nenhum evento próximo.</p>
        ) : (
          <ul className="space-y-2">
            {eventos.map((ev) => (
              <li key={ev.id} className="flex items-center justify-between text-sm">
                <span className="text-slate-700">{ev.titulo}</span>
                <span className="text-slate-400">
                  {new Date(ev.data_inicio).toLocaleDateString('pt-BR')}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-900">
            <Megaphone size={16} className="text-emerald-600" />
            Avisos não lidos
          </div>
          <Link to="/avisos" className="text-xs font-medium text-emerald-600">
            Ver tudo
          </Link>
        </div>
        {avisos.length === 0 ? (
          <p className="text-sm text-slate-400">Nenhum aviso novo.</p>
        ) : (
          <ul className="space-y-2">
            {avisos.map((av) => (
              <li key={av.id} className="text-sm text-slate-700">
                {av.titulo}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
