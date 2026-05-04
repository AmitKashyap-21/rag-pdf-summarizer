import React from 'react'

function statusBadge(status) {
  const colors = {
    ready: 'bg-green-100 text-green-800',
    processing: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
    uploaded: 'bg-blue-100 text-blue-800',
  }
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
      {status}
    </span>
  )
}

export default function DocumentCard({ doc, onDelete }) {
  return (
    <div className="bg-white rounded-lg shadow p-4 flex items-center justify-between gap-4">
      <div className="min-w-0 flex-1">
        <p className="font-medium text-gray-900 truncate">{doc.filename}</p>
        <p className="text-sm text-gray-500 mt-1">
          {doc.num_pages} pages · {doc.num_chunks} chunks ·{' '}
          {(doc.file_size / 1024).toFixed(1)} KB
        </p>
        <p className="text-xs text-gray-400 mt-1">
          {new Date(doc.created_at).toLocaleString()}
        </p>
      </div>
      <div className="flex items-center gap-3">
        {statusBadge(doc.status)}
        <button
          onClick={() => onDelete(doc.id)}
          className="text-red-500 hover:text-red-700 text-sm font-medium"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
