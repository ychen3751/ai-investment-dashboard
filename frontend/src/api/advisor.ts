import client from './client'

export interface AdvisorAnalysis {
  portfolio_score: number
  risk_score: number
  diversification_score: number
  market_beta: number | null
  sector_exposure: Array<{ sector: string; weight: number }>
  top_contributors: Array<{ symbol: string; pnl_pct: number; weight: number }>
  top_risks: Array<{ risk: string; detail: string; severity: string }>
  correlation_analysis: {
    available: boolean
    symbols?: string[]
    matrix?: number[][]
    average_correlation?: number
    pairs?: Array<{ pair: string; correlation: number }>
    message?: string
  }
  risk_metrics: {
    volatility_annualized?: number
    sharpe_ratio?: number
    max_drawdown?: number
    current_drawdown?: number
    beta?: number
    correlation?: number
    var_95?: number
  }
  portfolio_health: {
    holdings_count: number
    total_value: number
    total_cost: number
    top_holding_weight: number
    top3_holding_weight: number
    hhi: number
  }
  ai_summary: string
  beginner_explanation: string
  suggestions: string[]
}

export async function fetchAdvisorAnalysis(portfolioId: string): Promise<AdvisorAnalysis> {
  const { data } = await client.get(`/portfolios/${portfolioId}/advisor`)
  return data
}
