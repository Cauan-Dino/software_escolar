import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { alunoApi } from '../api/aluno'
import { TIPO_EVENTO_LABELS, type EventoCalendarioRead } from '../types/api'

function inicioAno(): string {
  return `${new Date().getFullYear()}-01-01`
}

function fimAno(): string {
  return `${new Date().getFullYear()}-12-31`
}

const TIPO_STYLES: Record<string, string> = {
  PROVA: 'bg-red-50 text-red-700',
  FERIADO: 'bg-slate-100 text-slate-600',
  REUNIAO: 'bg-amber-50 text-amber-700',
  EVENTO: 'bg-emerald-50 text-emerald-700',
  OUTRO: 'bg-slate-100 text-slate-600',
}

export function CalendarioPage() {
  const [eventos, setEventos] = useState<EventoCalendarioRead[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    alunoApi
      .eventos(inicioAno(), fimAno())
      .then((evs) =>
        setEventos(
          [...evs].sort((a, b) => a.data_inicio.localeCompare(b.data_inicio)),
        ),
      )
      .catch(() => setErro('Não foi possível carregar o calendário.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400">
        <Loader2 className="animate-spin" />
      </div>
    )
  }

  if (erro) {
    return <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{erro}</p>
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold text-slate-900">Calendário</h1>

      {eventos.length === 0 && <p className="text-sm text-slate-400">Nenhum evento cadastrado.</p>}

      <div className="space-y-2">
        {eventos.map((ev) => (
          <div key={ev.id} className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-900">{ev.titulo}</p>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${TIPO_STYLES[ev.tipo]}`}
              >
                {TIPO_EVENTO_LABELS[ev.tipo]}
              </span>
            </div>
            {ev.descricao && <p className="mt-1 text-sm text-slate-500">{ev.descricao}</p>}
            <p className="mt-2 text-xs text-slate-400">
              {new Date(ev.data_inicio).toLocaleDateString('pt-BR')}
              {ev.data_fim && ev.data_fim !== ev.data_inicio
                ? ` – ${new Date(ev.data_fim).toLocaleDateString('pt-BR')}`
                : ''}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
