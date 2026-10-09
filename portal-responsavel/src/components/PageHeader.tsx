import type { ReactNode } from 'react'

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: ReactNode
}) {
  return (
    <div className="mb-6 flex sm:mb-8 flex-wrap items-end justify-between gap-4 border-b border-slate-200 pb-5 sm:pb-6">
      <div className="min-w-0">
        <h1 className="font-display text-2xl sm:text-3xl font-semibold tracking-tight text-slate-900">
          {title}
        </h1>
        {subtitle && <p className="mt-1.5 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
