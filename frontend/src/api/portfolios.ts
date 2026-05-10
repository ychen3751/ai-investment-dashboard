import client from './client'
import { Portfolio, PortfolioCreate, Holding, HoldingCreate, Transaction, TransactionCreate, Performance } from '../types/portfolio'

export interface PortfolioSummary {
  total_value: number
  total_cost: number
  total_pnl: number
  total_pnl_pct: number
  day_pnl: number
  portfolio_count: number
  holding_count: number
}

export interface MarketIndex {
  symbol: string
  name: string
  value: number | null
  change: number | null
  change_pct: number | null
}

export interface DashboardData {
  portfolio: PortfolioSummary
  market: MarketIndex[]
}

export async function fetchDashboardSummary(): Promise<DashboardData> {
  const { data } = await client.get('/dashboard/summary')
  return data
}

export async function fetchPortfolios(): Promise<Portfolio[]> {
  const { data } = await client.get('/portfolios')
  return data
}

export async function createPortfolio(data: PortfolioCreate): Promise<Portfolio> {
  const { data: res } = await client.post('/portfolios', data)
  return res
}

export async function fetchPortfolio(id: string): Promise<Portfolio> {
  const { data } = await client.get(`/portfolios/${id}`)
  return data
}

export async function deletePortfolio(id: string): Promise<void> {
  await client.delete(`/portfolios/${id}`)
}

export async function fetchHoldings(portfolioId: string): Promise<Holding[]> {
  const { data } = await client.get(`/portfolios/${portfolioId}/holdings`)
  return data
}

export async function addHolding(portfolioId: string, data: HoldingCreate): Promise<Holding> {
  const { data: res } = await client.post(`/portfolios/${portfolioId}/holdings`, data)
  return res
}

export async function updateHolding(portfolioId: string, holdingId: string, data: { quantity: number; average_cost_basis: number }): Promise<Holding> {
  const { data: res } = await client.put(`/portfolios/${portfolioId}/holdings/${holdingId}`, data)
  return res
}

export async function removeHolding(portfolioId: string, holdingId: string): Promise<void> {
  await client.delete(`/portfolios/${portfolioId}/holdings/${holdingId}`)
}

export async function fetchTransactions(portfolioId: string): Promise<Transaction[]> {
  const { data } = await client.get(`/portfolios/${portfolioId}/transactions`)
  return data
}

export async function addTransaction(portfolioId: string, data: TransactionCreate): Promise<Transaction> {
  const { data: res } = await client.post(`/portfolios/${portfolioId}/transactions`, data)
  return res
}

export async function fetchPerformance(portfolioId: string): Promise<Performance> {
  const { data } = await client.get(`/portfolios/${portfolioId}/performance`)
  return data
}
