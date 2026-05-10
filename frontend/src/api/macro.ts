import client from './client'

export interface MacroIndicator {
  symbol: string
  name: string
  price: number | null
  change: number | null
  change_pct: number | null
  week_change_pct: number | null
  sparkline: number[]
}

export interface MacroSignal {
  signal: string
  explanation: string
}

export interface SectorInfo {
  name: string
  symbol: string
  daily_pct: number | null
  weekly_pct: number | null
  momentum: number | null
}

export interface EconomicEvent {
  event: string
  date: string
  impact: string
  volatility: string
}

export interface MacroOverview {
  market_regime: {
    regime: string
    confidence: number
    explanation: string
    bullish_pct: number
  }
  macro_indicators: MacroIndicator[]
  macro_signals: Record<string, MacroSignal>
  sector_rotation: SectorInfo[]
  economic_events: EconomicEvent[]
  ai_analysis: {
    narrative: string
    key_risks: string[]
    key_opportunities: string[]
  }
}

export async function fetchMacroOverview(): Promise<MacroOverview> {
  const { data } = await client.get('/macro/overview')
  return data
}
