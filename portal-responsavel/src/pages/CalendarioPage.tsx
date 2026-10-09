import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { calendarioApi } from '../api/calendario'
import { apiErrorMessage } from '../api/client'
import type { EventoCalendarioRead, TipoEvento } from '../types/api'
import { TIPO_EVENTO_LABELS } from '../types/api'
import { PageHeader } from '../components/PageHeader'

const TIPO_COLOR: Record<TipoEvento, string> = {
  PROVA: 'bg-red-50 text-red-700',
  FERIADO: 'bg-sky-50 text-sky-700',
  REUNIAO: 'bg-purple-50 text-purple-700',
  EVENTO: 'bg-emerald-50 text-emerald-700',
  OUTRO: 'bg-slate-100 text-slate-600',
}

export function CalendarioPage() {
  const [eventos, setEventos] = useState<EventoCalendarioRead[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    calendarioApi
      .listarEventos()
      .then(setEventos)
      .catch((err) => setErro(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader
        title="Calendário"
        subtitle={`${eventos.length} eventos nos próximos 60 dias`}
      />

      {erro && (
        <p className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{erro}</p>
      )}

      {loading ? (
        <div className="flex justify-center py-16 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : (
        <div className="space-y-2">
          {eventos.map((ev) => (
            <div
              key={ev.id}
              className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4"
            >
              <div className="w-20 shrink-0 text-center">
                <p className="text-xs text-slate-400">
                  {new Date(ev.data_inicio + 'T00:00').toLocaleDateString('pt-BR', {
                    day: '2-digit',
                    month: 'short',
                  })}
                </p>
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-slate-900">{ev.titulo}</p>
                {ev.descricao && (
                  <p className="truncate text-sm text-slate-500">{ev.descricao}</p>
                )}
              </div>
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-medium ${TIPO_COLOR[ev.tipo]}`}
              >
                {TIPO_EVENTO_LABELS[ev.tipo]}
              </span>
            </div>
          ))}
          {eventos.length === 0 && (
            <p className="py-8 text-center text-slate-400">
              Nenhum evento nos próximos 60 dias.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
