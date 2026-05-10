import { useState, useRef, useEffect, useCallback } from 'react'
import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'
import client from '../../api/client'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

const SUGGESTED_PROMPTS = [
  'Analyze NVDA',
  'Why is the market down?',
  'Explain VIX',
  'Options strategy for AAPL',
  'Analyze my portfolio risk',
  'Do you think Intel will rise?',
]

function extractSignal(text: string): string | null {
  const lower = text.toLowerCase()
  if (lower.includes('bullish')) return 'bullish'
  if (lower.includes('bearish')) return 'bearish'
  return null
}

function renderContent(text: string) {
  const lines = text.split('\n').filter(Boolean)
  const signal = extractSignal(text)
  return (
    <>
      {signal && (
        <div className="mb-2">
          <Badge variant={signal === 'bullish' ? 'success' : 'danger'}>{signal.toUpperCase()}</Badge>
        </div>
      )}
      {lines.map((line, i) => {
        if (line.startsWith('**') && line.endsWith('**')) {
          return <p key={i} className="text-sm font-semibold text-gray-100 mt-2 first:mt-0">{line.slice(2, -2)}</p>
        }
        if (line.startsWith('• ') || line.startsWith('- ')) {
          return (
            <p key={i} className="text-sm text-gray-300 pl-2 flex items-start gap-1.5 mt-0.5">
              <span className="text-primary-400 flex-shrink-0">•</span>
              <span>{line.replace(/^[•\-]\s*/, '')}</span>
            </p>
          )
        }
        if (line === '---') {
          return <hr key={i} className="border-gray-700 my-2" />
        }
        return <p key={i} className="text-sm text-gray-200 mt-1 first:mt-0">{line}</p>
      })}
    </>
  )
}

export function AIChat() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    { role: 'assistant', content: 'Hello! I\'m your AI Investing Assistant. Ask me about markets, portfolio analysis, or any investing concept.' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [lastTicker, setLastTicker] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Re-focus input after sending
  useEffect(() => {
    if (!loading && open) {
      inputRef.current?.focus()
    }
  }, [loading, open])

  const send = useCallback(async (text: string) => {
    const msg = text.trim()
    if (!msg || loading) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'user' as const, content: msg }])
    setLoading(true)
    try {
      const { data } = await client.post('/chat', { message: msg, last_ticker: lastTicker })
      const response = data.response || 'I couldn\'t generate a response. Please try rephrasing your question.'
      setMessages((prev) => [...prev, { role: 'assistant' as const, content: response }])
      if (data.ticker_context) setLastTicker(data.ticker_context)
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant' as const, content: 'Unable to retrieve market analysis right now. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }, [loading, lastTicker])

  const handleSend = useCallback(() => {
    if (input.trim()) send(input)
  }, [input, send])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  const showWelcome = messages.length === 1 && messages[0].role === 'assistant'

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-5 right-5 z-50 w-14 h-14 rounded-full bg-primary-600 hover:bg-primary-700 text-white shadow-xl flex items-center justify-center text-2xl transition-all duration-200 hover:scale-105 hover:shadow-primary-500/25"
          title="AI Investing Assistant"
        >
          💬
        </button>
      )}

      {open && (
        <div className="fixed bottom-5 right-5 z-50 w-[380px] max-w-[calc(100vw-40px)] h-[560px] max-h-[calc(100vh-100px)] bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-gray-900/95 flex-shrink-0">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-gain animate-pulse" />
              <span className="text-sm font-semibold text-gray-100">AI Assistant</span>
            </div>
            <button onClick={() => setOpen(false)} className="text-gray-500 hover:text-gray-300 text-lg leading-none p-1">&times;</button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[88%] rounded-xl px-3.5 py-2.5 ${
                  msg.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-800/80 text-gray-200'
                }`}>
                  {renderContent(msg.content)}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-800/80 rounded-xl px-4 py-3 max-w-[88%]">
                  <div className="flex gap-1 mb-1">
                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <p className="text-[11px] text-gray-500">Analyzing market conditions...</p>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick prompts — only before any user message */}
          {showWelcome && (
            <div className="px-4 pb-2 flex-shrink-0">
              <p className="text-[10px] text-gray-600 mb-2">Try asking:</p>
              <div className="flex flex-wrap gap-1.5">
                {SUGGESTED_PROMPTS.map((q) => (
                  <button key={q} onClick={() => send(q)}
                    className="text-[11px] px-2.5 py-1 rounded-full bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-gray-200 transition-colors">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="px-4 py-3 border-t border-gray-800 flex-shrink-0">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about markets..."
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
                disabled={loading}
              />
              <Button size="sm" onClick={handleSend} disabled={loading || !input.trim()}>
                {loading ? '...' : 'Send'}
              </Button>
            </div>
            <p className="text-[10px] text-gray-600 mt-1.5">Educational only — not financial advice.</p>
          </div>
        </div>
      )}
    </>
  )
}
