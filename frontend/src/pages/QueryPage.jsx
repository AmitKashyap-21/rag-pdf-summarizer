import React, { useState, useEffect } from 'react'
import { listDocuments, queryDocument } from '../api/client'

export default function QueryPage() {
  const [docs, setDocs] = useState([])
  const [selectedDoc, setSelectedDoc] = useState('')
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    listDocuments(0, 100, 'ready')
      .then(res => setDocs(res.data.documents))
      .catch(() => {})
  }, [])

  const handleQuery = async () => {
    if (!selectedDoc || !query.trim()) return
    setLoading(true)
    setError('')
    setResults(null)
    try {
      const res = await queryDocument(selectedDoc, { query, top_k: topK })
      setResults(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Query failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Query Document</h1>

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
          <label className="block text-sm font-medium text-gray-700 mb-1">Your Query</label>
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleQuery() } }}
            rows={3}
            placeholder="What are the main findings of this document?"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>

        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Top K results:</label>
          <input
            type="number"
            min={1}
            max={20}
            value={topK}
            onChange={e => setTopK(Number(e.target.value))}
            className="w-20 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>

        <button
          onClick={handleQuery}
          disabled={!selectedDoc || !query.trim() || loading}
          className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      {results && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Results for: <span className="text-indigo-600">"{results.query}"</span>
          </h2>
          <div className="space-y-3">
            {results.results.map((r, i) => (
              <div key={i} className="bg-white rounded-xl shadow p-5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-indigo-600">
                    #{i + 1} · Page {r.page_number}
                  </span>
                  <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full">
                    Score: {r.similarity_score?.toFixed(4)}
                  </span>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{r.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
