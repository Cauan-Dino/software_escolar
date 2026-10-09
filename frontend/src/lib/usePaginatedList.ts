import { useCallback, useEffect, useState } from 'react'
import { apiErrorMessage } from '../api/client'
import type { Page } from '../types/api'

const PAGE_SIZE = 50

/** Paginação real (limit/offset) para listagens grandes, com busca resetando a página. */
export function usePaginatedList<T>(
  fetcher: (params: { limit: number; offset: number }) => Promise<Page<T>>,
  deps: unknown[] = [],
) {
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState<T[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Volta para a primeira página sempre que os filtros (deps) mudam.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => setOffset(0), deps)

  const reload = useCallback(() => {
    setLoading(true)
    setError(null)
    fetcher({ limit: PAGE_SIZE, offset })
      .then((page) => {
        setData(page.items)
        setTotal(page.total)
      })
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset, ...deps])

  useEffect(() => {
    reload()
  }, [reload])

  return {
    data,
    total,
    loading,
    error,
    reload,
    offset,
    pageSize: PAGE_SIZE,
    hasPrev: offset > 0,
    hasNext: offset + PAGE_SIZE < total,
    goPrev: () => setOffset((o) => Math.max(0, o - PAGE_SIZE)),
    goNext: () => setOffset((o) => o + PAGE_SIZE),
  }
}
