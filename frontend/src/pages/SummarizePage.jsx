import React, { useState, useEffect } from 'react'
import { listDocuments, summarizeDocument } from '../api/client'
import ReactMarkdown from 'react-markdown'

export default function SummarizePage() {
  const [docs, setDocs] = useState([])
  const [selectedDoc, setSelectedDoc] = useState('')
  const [level, setLevel] = useState('medium')
  const [customPrompt, setCustomPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    listDocuments(0, 100, 'ready')
      .then(res => setDocs(res.data.documents))
      .catch(() => {})
  }, [])

  const handleSummarize = async () => {
    if (!selectedDoc) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await summarizeDocument(selectedDoc, {
        summary_level: level,
        custom_prompt: customPrompt || undefined,
        model: 'openai/gpt-3.5-turbo',
      })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Summarization failed')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (result?.summary) {
      navigator.clipboard.writeText(result.summary)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Summarize Document</h1>

      <div className="bg-white rounded-xl shadow p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Document</label>
          <select
            value={selectedDoc}
            onChange={e => setSelectedDoc(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          >
            <option value="">-- Choose a document --</option>
            {docs.map(d => (
              <option key={d.id} value={d.id}>{d.filename}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Summary Level</label>
          <div className="flex gap-4">
            {['brief', 'medium', 'detailed'].map(l => (
              <label key={l} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="level"
                  value={l}
                  checked={level === l}
                  onChange={() => setLevel(l)}
                  className="text-indigo-600"
                />
                <span className="capitalize text-sm text-gray-700">{l}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Custom Prompt (optional)</label>
          <textarea
            value={customPrompt}
            onChange={e => setCustomPrompt(e.target.value)}
            rows={3}
            placeholder="E.g. Focus on financial figures and key metrics..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>

        <button
          onClick={handleSummarize}
          disabled={!selectedDoc || loading}
          className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Generating summary...' : 'Generate Summary'}
        </button>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <div className="bg-white rounded-xl shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Summary</h2>
              <button onClick={handleCopy} className="text-sm text-indigo-600 hover:underline">
                {copied ? '✓ Copied!' : 'Copy'}
              </button>
            </div>
            <div className="prose prose-sm max-w-none text-gray-700">
              <ReactMarkdown>{result.summary}</ReactMarkdown>
            </div>
          </div>

          <div className="bg-gray-50 rounded-xl border p-4 text-sm text-gray-600 grid grid-cols-3 gap-4">
            <div>
              <p className="font-medium text-gray-700">Tokens used</p>
              <p>{result.tokens_used?.total?.toLocaleString() || 0}</p>
            </div>
            <div>
              <p className="font-medium text-gray-700">Est. cost</p>
              <p>${result.estimated_cost_usd?.toFixed(6)}</p>
            </div>
            <div>
              <p className="font-medium text-gray-700">Time</p>
              <p>{result.generation_time_ms}ms</p>
            </div>
          </div>

          {result.chunks_used?.length > 0 && (
            <div className="bg-white rounded-xl shadow p-6">
              <h3 className="font-semibold text-gray-800 mb-3">Source Chunks ({result.chunks_used.length})</h3>
              <div className="space-y-2">
                {result.chunks_used.map((c, i) => (
                  <div key={i} className="p-3 bg-gray-50 rounded-lg text-sm">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Page {c.page_number}</span>
                      <span>Score: {c.similarity_score?.toFixed(3)}</span>
                    </div>
                    <p className="text-gray-700 truncate">{c.preview}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
