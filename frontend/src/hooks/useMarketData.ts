import { useRef, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import client from '../api/client'
import { PriceTick, OHLCV } from '../types/common'

const POLL_INTERVAL = 30_000  // 30s
const STALE_THRESHOLD = 60_000  // 60s without update = stale

// ── Quote hook with stale detection ─────────────────────────────────────

export function useQuote(symbol: string) {
  const updatedAtRef = useRef<number>(0)

  const query = useQuery({
    queryKey: ['quote', symbol],
    queryFn: async (): Promise<{ data: PriceTick | null; fetchedAt: number }> => {
      const res = await client.get(`/market/quote/${symbol}`)
      const now = Date.now()
      updatedAtRef.current = now
      return { data: res.data, fetchedAt: now }
    },
    refetchInterval: POLL_INTERVAL,
    enabled: !!symbol,
    staleTime: 15_000,
    select: (result) => result.data,
  })

  const isStale = query.isSuccess && (Date.now() - updatedAtRef.current > STALE_THRESHOLD)

  return { ...query, isStale }
}

// ── Batch multiple quotes at once ───────────────────────────────────────

export function useQuotes(symbols: string[]) {
  const symbolsKey = [...symbols].sort().join(',')

  return useQuery({
    queryKey: ['quotes', symbolsKey],
    queryFn: async (): Promise<Record<string, PriceTick | null>> => {
      const entries = await Promise.all(
        symbols.map(async (sym) => {
          try {
            const { data } = await client.get(`/market/quote/${sym}`)
            return [sym, data] as const
          } catch {
            return [sym, null] as const
          }
        }),
      )
      return Object.fromEntries(entries)
    },
    refetchInterval: POLL_INTERVAL,
    enabled: symbols.length > 0,
    staleTime: 15_000,
  })
}

// ── OHLCV history ──────────────────────────────────────────────────────

export function useHistory(symbol: string, interval = '1d', range = '1mo') {
  return useQuery({
    queryKey: ['history', symbol, interval, range],
    queryFn: async (): Promise<OHLCV[]> => {
      const { data } = await client.get(`/market/history/${symbol}`, {
        params: { interval, range },
      })
      return data
    },
    staleTime: 60_000,
    enabled: !!symbol,
  })
}

// ── Symbol search (autocomplete) ───────────────────────────────────────

export function useSymbolSearch(query: string) {
  return useQuery({
    queryKey: ['symbolSearch', query],
    queryFn: async (): Promise<Array<{ symbol: string; name: string; exchange: string; type: string }>> => {
      const { data } = await client.get('/market/search', { params: { q: query } })
      return data
    },
    enabled: query.length >= 1,
    staleTime: 30_000,
  })
}

// ── WebSocket bridge — replaces polling with push updates when available ──

export function useWebSocketQuotes(symbols: string[]) {
  const queryClient = useQueryClient()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const attemptRef = useRef(0)

  useEffect(() => {
    if (!symbols.length) return

    const connect = () => {
      const params = symbols.join(',')
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/prices?symbols=${params}`)

      ws.onopen = () => { attemptRef.current = 0 }

      ws.onmessage = (event) => {
        try {
          const tick = JSON.parse(event.data)
          if (tick.symbol && tick.price != null) {
            // Update the React Query cache directly — no extra re-render
            queryClient.setQueryData(['quote', tick.symbol], { data: tick, fetchedAt: Date.now() })
          }
        } catch { /* ignore malformed messages */ }
      }

      ws.onclose = () => {
        const delay = Math.min(1000 * Math.pow(2, attemptRef.current), 30_000)
        attemptRef.current++
        reconnectTimer.current = setTimeout(connect, delay)
      }

      wsRef.current = ws
    }

    connect()

    return () => {
      clearTimeout(reconnectTimer.current)
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [symbols.join(','), queryClient])
}
