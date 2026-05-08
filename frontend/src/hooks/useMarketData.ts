import { useQuery } from '@tanstack/react-query'
import client from '../api/client'
import { PriceTick, OHLCV } from '../types/common'

export function useQuote(symbol: string) {
  return useQuery({
    queryKey: ['quote', symbol],
    queryFn: async (): Promise<PriceTick | null> => {
      const { data } = await client.get(`/market/quote/${symbol}`)
      return data
    },
    refetchInterval: 30_000,
    enabled: !!symbol,
  })
}

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

export function useSymbolSearch(query: string) {
  return useQuery({
    queryKey: ['symbolSearch', query],
    queryFn: async (): Promise<Array<{ symbol: string; name: string; exchange: string; type: string }>> => {
      if (!query || query.length < 1) return []
      const { data } = await client.get('/market/search', { params: { q: query } })
      return data
    },
    enabled: query.length >= 1,
    staleTime: 30_000,
  })
}
