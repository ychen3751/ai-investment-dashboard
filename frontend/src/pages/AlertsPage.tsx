import { Card } from '../components/ui/Card'

export function AlertsPage() {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-bold">Alerts</h2>
      <Card title="Your Alerts">
        <p className="text-gray-500 text-sm">Price and volume alerts coming in Phase 4.</p>
      </Card>
    </div>
  )
}
