import client from './client'

export interface StrategyRecommendation {
  strategy: string
  bias: string
  risk_level: string
  max_profit: string
  max_loss: string
  breakeven: string
  description: string
  ai_explanation: string
  capital_required: string
  beginner_friendly: boolean
}

export async function recommendStrategy(params: {
  bias: string
  volatility: string
  risk_tolerance: string
  capital: number
  time_horizon: string
}): Promise<StrategyRecommendation> {
  const { data } = await client.post('/options/strategy', null, { params })
  return data
}
