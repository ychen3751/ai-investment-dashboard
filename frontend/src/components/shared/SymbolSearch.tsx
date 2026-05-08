import { useState, useRef, useEffect } from 'react'
import { useSymbolSearch } from '../../hooks/useMarketData'
import { Input } from '../ui/Input'
import { useClickAway } from '../../hooks/useClickAway'

interface SymbolSearchProps {
  value?: string
  onChange?: (value: string) => void
  onSelect?: (symbol: string, name: string) => void
  placeholder?: string
}

export function SymbolSearch({ value: controlledValue, onChange, onSelect, placeholder = 'Search symbols...' }: SymbolSearchProps) {
  const [internalQuery, setInternalQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [selected, setSelected] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const isControlled = controlledValue !== undefined
  const query = isControlled ? controlledValue : internalQuery

  const { data: results, isLoading } = useSymbolSearch(query)

  useClickAway(ref, () => setIsOpen(false))

  const handleSelect = (symbol: string, name: string) => {
    setSelected(true)
    setIsOpen(false)
    const s = symbol.toUpperCase().trim()
    if (onChange) onChange(s)
    if (onSelect) onSelect(s, name)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelected(false)
    const val = e.target.value.toUpperCase()
    if (!isControlled) setInternalQuery(val)
    if (onChange) onChange(val)
    setIsOpen(true)
  }

  // Reset selected state when query changes externally
  useEffect(() => {
    setSelected(false)
  }, [controlledValue])

  return (
    <div ref={ref} className="relative">
      <Input
        value={query}
        onChange={handleChange}
        onFocus={() => setIsOpen(true)}
        placeholder={placeholder}
      />
      {isOpen && query && !selected && (
        <div className="absolute z-50 mt-1 w-full bg-gray-900 border border-gray-700 rounded-lg shadow-xl max-h-60 overflow-y-auto">
          {isLoading && <div className="p-3 text-sm text-gray-500">Searching...</div>}
          {results && results.length === 0 && !isLoading && (
            <div className="p-3 text-sm text-gray-500">No results &mdash; type ticker directly</div>
          )}
          {results?.map((r) => (
            <button
              key={r.symbol}
              type="button"
              className="w-full text-left px-3 py-2 hover:bg-gray-800 transition-colors"
              onMouseDown={(e) => {
                e.preventDefault()
                handleSelect(r.symbol, r.name)
              }}
            >
              <span className="text-sm font-medium text-gray-200">{r.symbol}</span>
              <span className="text-xs text-gray-500 ml-2">{r.name}</span>
              <span className="text-xs text-gray-600 ml-1">{r.exchange}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
