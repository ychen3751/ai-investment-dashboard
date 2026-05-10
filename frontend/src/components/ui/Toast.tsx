import { useState, useCallback, useEffect } from 'react'
import clsx from 'clsx'

type ToastType = 'success' | 'error' | 'info'

interface Toast {
  id: number
  message: string
  type: ToastType
}

let toastId = 0
let addToastFn: ((msg: string, type?: ToastType) => void) | null = null

export function toast(message: string, type: ToastType = 'info') {
  addToastFn?.(message, type)
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = ++toastId
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  useEffect(() => {
    addToastFn = addToast
    return () => { addToastFn = null }
  }, [addToast])

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={clsx(
            'px-4 py-3 rounded-lg shadow-xl text-sm font-medium animate-slide-up',
            'backdrop-blur-xl border',
            t.type === 'success' && 'bg-green-900/80 border-green-700/50 text-green-300',
            t.type === 'error' && 'bg-red-900/80 border-red-700/50 text-red-300',
            t.type === 'info' && 'bg-gray-900/80 border-gray-700/50 text-gray-200',
          )}
          style={{ animation: 'slide-up 0.2s ease-out' }}
        >
          {t.message}
        </div>
      ))}
      <style>{`
        @keyframes slide-up {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
