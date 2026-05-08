import { useEffect, useRef, useCallback } from 'react'
import { useWsStore } from '../store/wsStore'

const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/prices`

export function useWebSocket(symbols: string[]) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout>>()
  const reconnectAttempt = useRef(0)

  const updatePrice = useWsStore((s) => s.updatePrice)
  const removeSymbols = useWsStore((s) => s.removeSymbols)

  const connect = useCallback(() => {
    if (!symbols.length) return

    const symbolParam = symbols.join(',')
    const ws = new WebSocket(`${WS_BASE}?symbols=${symbolParam}`)

    ws.onopen = () => {
      reconnectAttempt.current = 0
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        updatePrice(data.symbol, {
          symbol: data.symbol,
          price: data.price,
          change: data.change,
          change_pct: data.change_pct,
          volume: data.volume,
          timestamp: data.timestamp,
        })
      } catch {
        // ignore parse errors
      }
    }

    ws.onclose = () => {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempt.current), 30000)
      reconnectAttempt.current++
      reconnectTimeout.current = setTimeout(connect, delay)
    }

    wsRef.current = ws
  }, [symbols, updatePrice])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimeout.current)
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      removeSymbols(symbols)
    }
  }, [connect, symbols, removeSymbols])
}
