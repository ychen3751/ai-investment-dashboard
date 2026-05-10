export interface OptionPosition {
  id: string
  underlying_symbol: string
  option_type: 'call' | 'put'
  side: 'long' | 'short'
  strike_price: number
  expiration_date: string
  contracts: number
  premium_per_contract: number
  cost_basis: number | null
  market_value: number | null
  unrealized_pnl: number | null
  unrealized_pnl_pct: number | null
  current_price: number | null
  status: string | null
  created_at: string
  updated_at: string
}

export interface OptionPositionCreate {
  underlying_symbol: string
  option_type: 'call' | 'put'
  side: 'long' | 'short'
  strike_price: number
  expiration_date: string
  contracts: number
  premium_per_contract: number
}

export interface OptionPositionUpdate {
  contracts: number
  premium_per_contract: number
}
