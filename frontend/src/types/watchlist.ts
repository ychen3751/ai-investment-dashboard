export interface Watchlist {
  id: string
  name: string
  created_at: string
  item_count: number
  items: WatchlistItem[]
}

export interface WatchlistCreate {
  name: string
}

export interface WatchlistItem {
  id: string
  symbol: string
  notes: string | null
  added_at: string
  current_price: number | null
  change: number | null
  change_pct: number | null
}

export interface WatchlistItemCreate {
  symbol: string
  notes?: string
}
