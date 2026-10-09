import { ChevronLeft, ChevronRight } from 'lucide-react'

export function Pagination({
  offset,
  pageSize,
  total,
  hasPrev,
  hasNext,
  onPrev,
  onNext,
}: {
  offset: number
  pageSize: number
  total: number
  hasPrev: boolean
  hasNext: boolean
  onPrev: () => void
  onNext: () => void
}) {
  if (total === 0) return null
  const inicio = offset + 1
  const fim = Math.min(offset + pageSize, total)

  return (
    <div className="mt-4 flex items-center justify-between text-sm text-slate-500">
      <span>
        Mostrando {inicio}–{fim} de {total}
      </span>
      <div className="flex gap-2">
        <button
          onClick={onPrev}
          disabled={!hasPrev}
          className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-medium text-slate-600 shadow-card transition-colors hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronLeft size={15} />
          Anterior
        </button>
        <button
          onClick={onNext}
          disabled={!hasNext}
          className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-medium text-slate-600 shadow-card transition-colors hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Próxima
          <ChevronRight size={15} />
        </button>
      </div>
    </div>
  )
}
