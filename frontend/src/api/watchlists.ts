import client from './client'
import { Watchlist, WatchlistCreate, WatchlistItemCreate } from '../types/watchlist'

export async function fetchWatchlists(): Promise<Watchlist[]> {
  const { data } = await client.get('/watchlists')
  return data
}

export async function createWatchlist(data: WatchlistCreate): Promise<Watchlist> {
  const { data: res } = await client.post('/watchlists', data)
  return res
}

export async function deleteWatchlist(id: string): Promise<void> {
  await client.delete(`/watchlists/${id}`)
}

export async function addWatchlistItem(watchlistId: string, data: WatchlistItemCreate): Promise<void> {
  await client.post(`/watchlists/${watchlistId}/items`, data)
}

export async function removeWatchlistItem(watchlistId: string, itemId: string): Promise<void> {
  await client.delete(`/watchlists/${watchlistId}/items/${itemId}`)
}

export interface WatchlistSignal {
  ticker: string
  signal: string
  confidence: number
  summary: string
  momentum_score: number
  trend: string
  indicators: {
    rsi: number
    macd: string
    volume_spike: boolean
    above_sma20: boolean
    above_sma50: boolean
    day_change_pct: number
    week_change_pct: number
  }
}

export async function fetchWatchlistSignals(): Promise<WatchlistSignal[]> {
  const { data } = await client.get('/watchlists/signals/all')
  return data
}
