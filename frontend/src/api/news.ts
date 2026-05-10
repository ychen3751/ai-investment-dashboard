import client from './client'

export interface NewsItem {
  title: string
  symbol: string
  publisher: string
  published: string | null
  link: string
  sentiment: string
  score: number
  sector: string
}

export interface SectorImpact {
  sector: string
  sentiment: string
  confidence: number
  headline_count: number
}

export interface TickerImpact {
  symbol: string
  sentiment: string
  confidence: number
  headline_count: number
}

export interface MacroTheme {
  theme: string
  sentiment: string
  headline_count: number
}

export interface MarketNewsSummary {
  overall_sentiment: string
  confidence: number
  market_summary: string
  top_headlines: NewsItem[]
  sector_impacts: SectorImpact[]
  macro_themes: MacroTheme[]
  ticker_impacts: TickerImpact[]
  timestamp: string
}

export async function fetchMarketNewsSummary(): Promise<MarketNewsSummary> {
  const { data } = await client.get('/news/market-summary')
  return data
}
