import { AlertTriangle, Loader2 } from 'lucide-react'

export function LoadingRow({ colSpan }: { colSpan: number }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-5 py-10 text-center text-slate-400">
        <Loader2 className="mx-auto mb-2 animate-spin" size={20} />
        Carregando...
      </td>
    </tr>
  )
}

export function ErrorRow({ colSpan, message }: { colSpan: number; message: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-5 py-10 text-center text-red-600">
        <AlertTriangle className="mx-auto mb-2" size={20} />
        {message}
      </td>
    </tr>
  )
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
      <AlertTriangle size={16} />
      {message}
    </div>
  )
}
