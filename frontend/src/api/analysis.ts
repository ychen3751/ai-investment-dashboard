import client from './client'
import { AnalysisResponse } from '../types/analysis'

export async function fetchFundamentalAnalysis(symbol: string): Promise<AnalysisResponse> {
  const { data } = await client.get(`/analysis/fundamental/${symbol}`)
  return data
}
