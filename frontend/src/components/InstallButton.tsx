import { useEffect, useState } from 'react'
import { Download, Share, X } from 'lucide-react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

function isStandalone() {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  )
}

function isIos() {
  return /iphone|ipad|ipod/i.test(navigator.userAgent)
}

/**
 * Botão "Instalar app".
 * - Chrome/Edge/Android: usa o evento `beforeinstallprompt` e abre o diálogo nativo.
 * - iOS (Safari não tem esse evento): mostra o passo a passo "Adicionar à Tela de Início".
 * - Já instalado (modo standalone): não renderiza nada.
 */
export function InstallButton({ variant = 'sidebar' }: { variant?: 'sidebar' | 'compact' }) {
  const [promptEvent, setPromptEvent] = useState<BeforeInstallPromptEvent | null>(null)
  const [instalado, setInstalado] = useState(() => isStandalone())
  const [ajudaIos, setAjudaIos] = useState(false)

  useEffect(() => {
    const onPrompt = (e: Event) => {
      e.preventDefault()
      setPromptEvent(e as BeforeInstallPromptEvent)
    }
    const onInstalled = () => {
      setInstalado(true)
      setPromptEvent(null)
    }
    window.addEventListener('beforeinstallprompt', onPrompt)
    window.addEventListener('appinstalled', onInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', onPrompt)
      window.removeEventListener('appinstalled', onInstalled)
    }
  }, [])

  const ios = isIos()
  if (instalado || (!promptEvent && !ios)) return null

  async function instalar() {
    if (promptEvent) {
      await promptEvent.prompt()
      const { outcome } = await promptEvent.userChoice
      if (outcome === 'accepted') setInstalado(true)
      setPromptEvent(null)
    } else {
      setAjudaIos(true)
    }
  }

  return (
    <>
      {variant === 'sidebar' ? (
        <button
          onClick={instalar}
          className="mx-3 mb-3 flex w-[calc(100%-1.5rem)] items-center gap-3 rounded-lg border border-emerald-400/30 bg-emerald-400/10 px-3 py-2 text-left text-sm font-medium text-emerald-100 transition-colors hover:bg-emerald-400/20"
        >
          <Download size={16} className="shrink-0 text-emerald-300" />
          Instalar aplicativo
        </button>
      ) : (
        <button
          onClick={instalar}
          title="Instalar aplicativo"
          aria-label="Instalar aplicativo"
          className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-400/15 text-emerald-200 ring-1 ring-emerald-300/30 transition-colors hover:bg-emerald-400/25"
        >
          <Download size={16} />
        </button>
      )}

      {ajudaIos && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-emerald-950/50 p-4 backdrop-blur-[2px] sm:items-center"
          onClick={() => setAjudaIos(false)}
        >
          <div
            className="w-full max-w-sm rounded-2xl bg-white p-5 text-slate-800 shadow-lift"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-base font-semibold">Instalar no iPhone / iPad</h2>
              <button
                onClick={() => setAjudaIos(false)}
                aria-label="Fechar"
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>
            <ol className="space-y-2 text-sm text-slate-600">
              <li className="flex items-start gap-2">
                <span className="font-semibold text-emerald-700">1.</span>
                <span>
                  Toque em <Share size={14} className="mx-0.5 inline -translate-y-px" />{' '}
                  <strong>Compartilhar</strong> na barra do Safari.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-semibold text-emerald-700">2.</span>
                <span>
                  Escolha <strong>Adicionar à Tela de Início</strong>.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-semibold text-emerald-700">3.</span>
                <span>
                  Toque em <strong>Adicionar</strong>.
                </span>
              </li>
            </ol>
          </div>
        </div>
      )}
    </>
  )
}
