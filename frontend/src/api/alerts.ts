import client from './client'

export interface Alert {
  id: string
  symbol: string
  alert_type: string
  condition: Record<string, unknown>
  is_active: boolean
  triggered_at: string | null
  last_checked_at: string | null
  created_at: string
}

export interface AlertCreate {
  symbol: string
  alert_type: string
  condition: Record<string, unknown>
}

export interface AlertUpdate {
  is_active?: boolean
  condition?: Record<string, unknown>
}

export async function fetchAlerts(isActive?: boolean): Promise<Alert[]> {
  const params = isActive !== undefined ? { is_active: isActive } : undefined
  const { data } = await client.get('/alerts', { params })
  return data
}

export async function createAlert(data: AlertCreate): Promise<Alert> {
  const { data: res } = await client.post('/alerts', data)
  return res
}

export async function updateAlert(id: string, data: AlertUpdate): Promise<Alert> {
  const { data: res } = await client.put(`/alerts/${id}`, data)
  return res
}

export async function deleteAlert(id: string): Promise<void> {
  await client.delete(`/alerts/${id}`)
}
