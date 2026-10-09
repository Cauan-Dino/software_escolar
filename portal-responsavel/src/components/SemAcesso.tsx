import { ShieldAlert } from 'lucide-react'

export function SemAcesso() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-slate-200 bg-white py-16 text-center">
      <ShieldAlert className="text-slate-300" size={32} />
      <p className="text-sm text-slate-500">
        Você não tem acesso a este aluno, ou ele não foi encontrado.
      </p>
    </div>
  )
}
