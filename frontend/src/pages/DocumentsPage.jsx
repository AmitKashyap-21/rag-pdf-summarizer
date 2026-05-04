import React, { useState, useEffect, useCallback } from 'react'
import { listDocuments, deleteDocument } from '../api/client'
import DocumentCard from '../components/DocumentCard'

export default function DocumentsPage() {
  const [docs, setDocs] = useState([])
  const [total, setTotal] = useState(0)
  const [skip, setSkip] = useState(0)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const limit = 10

  const fetchDocs = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await listDocuments(skip, limit, statusFilter)
      setDocs(res.data.documents)
      setTotal(res.data.total_count)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }, [skip, statusFilter])

  useEffect(() => { fetchDocs() }, [fetchDocs])

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this document?')) return
    try {
      await deleteDocument(id)
      fetchDocs()
    } catch (err) {
      alert(err.response?.data?.detail || 'Delete failed')
    }
  }

  const filtered = search
    ? docs.filter(d => d.filename.toLowerCase().includes(search.toLowerCase()))
    : docs

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Documents ({total})</h1>
        <button onClick={fetchDocs} className="text-sm text-indigo-600 hover:underline">Refresh</button>
      </div>

      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Search by filename..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
        <select
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setSkip(0) }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        >
          <option value="">All statuses</option>
          <option value="ready">Ready</option>
          <option value="processing">Processing</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {error && <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm mb-4">{error}</div>}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-gray-400">No documents found</div>
      ) : (
        <div className="space-y-3">
          {filtered.map(doc => (
            <DocumentCard key={doc.id} doc={doc} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {total > limit && (
        <div className="flex justify-center gap-3 mt-6">
          <button
            disabled={skip === 0}
            onClick={() => setSkip(s => Math.max(0, s - limit))}
            className="px-4 py-2 text-sm border rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-gray-600">
            {skip + 1}–{Math.min(skip + limit, total)} of {total}
          </span>
          <button
            disabled={skip + limit >= total}
            onClick={() => setSkip(s => s + limit)}
            className="px-4 py-2 text-sm border rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
