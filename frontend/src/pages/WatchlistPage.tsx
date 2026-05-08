import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Spinner } from '../components/ui/Spinner'
import { PriceChange } from '../components/shared/PriceChange'
import { SymbolSearch } from '../components/shared/SymbolSearch'
import { fetchWatchlists, createWatchlist, deleteWatchlist, addWatchlistItem, removeWatchlistItem } from '../api/watchlists'
import { Watchlist } from '../types/watchlist'
import { num, fmtPct, fmtCurrency as fmtCurr } from '../utils/formatters'

function fmtMarketCap(n: number | null | undefined) {
  const v = num(n)
  if (n == null || v === 0) return '-'
  if (Math.abs(v) >= 1e12) return `$${(v / 1e12).toFixed(2)}T`
  if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(2)}B`
  if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(2)}M`
  return fmtCurr(v)
}

export function WatchlistPage() {
  const qc = useQueryClient()
  const [activeTab, setActiveTab] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [addSymbol, setAddSymbol] = useState('')

  const { data: watchlists, isLoading } = useQuery({ queryKey: ['watchlists'], queryFn: fetchWatchlists })

  const activeWatchlist: Watchlist | undefined = watchlists?.find((w) => w.id === activeTab) || watchlists?.[0]

  const createMut = useMutation({
    mutationFn: () => createWatchlist({ name: newName }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['watchlists'] }); setShowCreate(false); setNewName('') },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteWatchlist(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlists'] }),
  })

  const addItemMut = useMutation({
    mutationFn: (wlId: string) => addWatchlistItem(wlId, { symbol: addSymbol.toUpperCase() }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['watchlists'] }); setAddSymbol('') },
  })

  const removeItemMut = useMutation({
    mutationFn: ({ wlId, itemId }: { wlId: string; itemId: string }) => removeWatchlistItem(wlId, itemId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlists'] }),
  })

  if (isLoading) return <Spinner />

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Watchlists</h2>
        <Button onClick={() => setShowCreate(!showCreate)}>{showCreate ? 'Cancel' : 'New Watchlist'}</Button>
      </div>

      {showCreate && (
        <Card className="flex gap-3 items-end">
          <Input label="Watchlist Name" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Tech stocks" />
          <Button onClick={() => createMut.mutate()} disabled={!newName || createMut.isPending}>Create</Button>
        </Card>
      )}

      {(!watchlists || watchlists.length === 0) ? (
        <Card><p className="text-gray-500 text-sm">No watchlists yet.</p></Card>
      ) : (
        <>
          <div className="flex gap-2 border-b border-gray-800 pb-2 overflow-x-auto">
            {watchlists.map((wl) => (
              <button
                key={wl.id}
                onClick={() => { setActiveTab(wl.id); setAddSymbol('') }}
                className={`px-3 py-1.5 text-sm rounded-t whitespace-nowrap transition-colors ${
                  activeWatchlist?.id === wl.id ? 'bg-gray-800 text-gray-100 border-b-2 border-primary-500' : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {wl.name} ({wl.item_count})
              </button>
            ))}
          </div>

          {activeWatchlist && (
            <Card>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">{activeWatchlist.name}</h3>
                <div className="flex gap-2">
                  <div className="flex gap-1">
                    <SymbolSearch onSelect={(sym) => setAddSymbol(sym)} placeholder="Add symbol..." />
                    {addSymbol && (
                      <Button size="sm" onClick={() => addItemMut.mutate(activeWatchlist.id)} disabled={addItemMut.isPending}>+</Button>
                    )}
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => deleteMut.mutate(activeWatchlist.id)}>Delete</Button>
                </div>
              </div>

              {activeWatchlist.items.length === 0 ? (
                <p className="text-gray-500 text-sm">No symbols. Search and add tickers above.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-800 text-gray-500">
                        <th className="text-left py-2 px-2">Symbol</th>
                        <th className="text-right py-2 px-2">Price</th>
                        <th className="text-right py-2 px-2">Change</th>
                        <th className="text-right py-2 px-2">Change %</th>
                        <th className="py-2 px-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeWatchlist.items.map((item) => (
                        <tr key={item.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                          <td className="py-2 px-2 font-medium">{item.symbol}</td>
                          <td className="py-2 px-2 text-right">{fmtCurr(item.current_price)}</td>
                          <td className="py-2 px-2 text-right">{item.change != null ? <PriceChange value={num(item.change)} pct={num(item.change_pct)} /> : '-'}</td>
                          <td className="py-2 px-2 text-right">{item.change_pct != null ? fmtPct(item.change_pct) : '-'}</td>
                          <td className="py-2 px-2 text-right">
                            <Button variant="ghost" size="sm" onClick={() => removeItemMut.mutate({ wlId: activeWatchlist.id, itemId: item.id })}>✕</Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          )}
        </>
      )}
    </div>
  )
}
