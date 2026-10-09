import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { pessoasApi } from '../api/pessoas'
import { apiErrorMessage } from '../api/client'
import type { AlunoRead } from '../types/api'

interface FilhoContextValue {
  filhos: AlunoRead[]
  filhoAtivo: AlunoRead | null
  carregando: boolean
  erro: string | null
  selecionarFilho: (alunoId: number) => void
  recarregar: () => void
}

const FilhoContext = createContext<FilhoContextValue | undefined>(undefined)

const STORAGE_KEY = 'filho_ativo_id'

export function FilhoProvider({ children }: { children: ReactNode }) {
  const [filhos, setFilhos] = useState<AlunoRead[]>([])
  const [filhoAtivoId, setFilhoAtivoId] = useState<number | null>(() => {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? Number(raw) : null
  })
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  function carregar() {
    setCarregando(true)
    setErro(null)
    pessoasApi
      .meusFilhos()
      .then((lista) => {
        setFilhos(lista)
        setFilhoAtivoId((atual) => {
          if (atual && lista.some((f) => f.id === atual)) return atual
          return lista[0]?.id ?? null
        })
      })
      .catch((err) => setErro(apiErrorMessage(err)))
      .finally(() => setCarregando(false))
  }

  useEffect(carregar, [])

  useEffect(() => {
    if (filhoAtivoId) localStorage.setItem(STORAGE_KEY, String(filhoAtivoId))
  }, [filhoAtivoId])

  const filhoAtivo = useMemo(
    () => filhos.find((f) => f.id === filhoAtivoId) ?? null,
    [filhos, filhoAtivoId],
  )

  const value = useMemo<FilhoContextValue>(
    () => ({
      filhos,
      filhoAtivo,
      carregando,
      erro,
      selecionarFilho: (alunoId: number) => setFilhoAtivoId(alunoId),
      recarregar: carregar,
    }),
    [filhos, filhoAtivo, carregando, erro],
  )

  return <FilhoContext.Provider value={value}>{children}</FilhoContext.Provider>
}

export function useFilho() {
  const ctx = useContext(FilhoContext)
  if (!ctx) throw new Error('useFilho deve ser usado dentro de FilhoProvider')
  return ctx
}
