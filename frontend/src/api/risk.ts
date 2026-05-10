import client from './client'

export interface RiskSummary {
  data_available: boolean
  n_days?: number
  portfolio_value?: number
  volatility?: { daily: number | null; annualized: number | null }
  sharpe_ratio?: number | null
  drawdown?: { max_pct: number; current_pct: number }
  value_at_risk?: {
    var_95_pct: number; cvar_95_pct: number
    var_95_value: number; cvar_95_value: number
    var_99_pct: number; cvar_99_pct: number
  }
  beta?: {
    beta?: number; alpha?: number; correlation?: number
    r_squared?: number; benchmark?: string
    error?: string
  }
  concentration?: {
    total_value?: number
    top_holdings?: Array<{ symbol: string; value: number; pct: number }>
    hhi?: number
    sectors?: Record<string, number> | null
    sectors_unavailable?: boolean
    error?: string
  }
  error?: string
}

export async function fetchRiskSummary(portfolioId: string): Promise<RiskSummary> {
  const { data } = await client.get(`/risk/summary/${portfolioId}`)
  return data
}

export async function fetchCorrelation(portfolioId: string): Promise<{
  symbols: string[]
  matrix: number[][]
  n_days: number
  error?: string
}> {
  const { data } = await client.get(`/risk/correlation/${portfolioId}`)
  return data
}
