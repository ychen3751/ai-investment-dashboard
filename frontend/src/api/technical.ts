import client from './client'
import { TechnicalAnalysis } from '../types/technical'

export async function fetchTechnicalAnalysis(symbol: string, interval = '1d', range = '3mo'): Promise<TechnicalAnalysis> {
  const { data } = await client.get(`/technical/${symbol}/all`, {
    params: { interval, range },
  })
  return data
}
