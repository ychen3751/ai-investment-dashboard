import { create } from 'zustand'

interface PriceTick {
  symbol: string
  price: number
  change: number
  change_pct: number
  volume: number
  timestamp: string
}

interface WsState {
  prices: Record<string, PriceTick>
  updatePrice: (symbol: string, tick: PriceTick) => void
  removeSymbols: (symbols: string[]) => void
}

export const useWsStore = create<WsState>((set) => ({
  prices: {},
  updatePrice: (symbol, tick) =>
    set((state) => ({
      prices: { ...state.prices, [symbol]: tick },
    })),
  removeSymbols: (symbols) =>
    set((state) => {
      const newPrices = { ...state.prices }
      symbols.forEach((s) => delete newPrices[s])
      return { prices: newPrices }
    }),
}))
