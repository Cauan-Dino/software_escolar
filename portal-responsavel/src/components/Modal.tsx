import { useEffect, type ReactNode } from 'react'
import { X } from 'lucide-react'

export function Modal({
  title,
  onClose,
  children,
}: {
  title: string
  onClose: () => void
  children: ReactNode
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-emerald-950/45 sm:items-center sm:px-4 backdrop-blur-[3px]"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="animate-rise max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-2xl sm:max-h-[90vh] sm:rounded-2xl bg-white shadow-lift ring-1 ring-slate-900/5"
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-4 sm:px-6">
          <h2 className="font-display text-lg font-semibold text-slate-900">{title}</h2>
          <button
            onClick={onClose}
            aria-label="Fechar"
            className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
          >
            <X size={18} />
          </button>
        </div>
        <div className="px-4 py-5 sm:px-6">{children}</div>
      </div>
    </div>
  )
}
