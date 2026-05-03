import React, { useState, useRef, useCallback } from 'react'
import { uploadDocuments } from '../api/client'

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState([])
  const [progress, setProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')
  const inputRef = useRef()

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const dropped = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf')
    setFiles(prev => [...prev, ...dropped])
  }, [])

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => setIsDragging(false)

  const handleFileInput = (e) => {
    const selected = Array.from(e.target.files).filter(f => f.type === 'application/pdf')
    setFiles(prev => [...prev, ...selected])
  }

  const removeFile = (index) => setFiles(prev => prev.filter((_, i) => i !== index))

  const handleUpload = async () => {
    if (!files.length) return
    setUploading(true)
    setError('')
    setResults(null)
    try {
      const res = await uploadDocuments(files, setProgress)
      setResults(res.data)
      setFiles([])
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Upload failed')
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Upload PDF Documents</h1>

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-indigo-400 bg-white'
        }`}
      >
        <div className="text-5xl mb-4">📄</div>
        <p className="text-lg font-medium text-gray-700">Drag & drop PDF files here</p>
        <p className="text-sm text-gray-500 mt-1">or click to browse</p>
        <p className="text-xs text-gray-400 mt-2">Max {50}MB per file</p>
        <input ref={inputRef} type="file" accept=".pdf" multiple className="hidden" onChange={handleFileInput} />
      </div>

      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          <h2 className="font-medium text-gray-700">Selected files ({files.length})</h2>
          {files.map((f, i) => (
            <div key={i} className="flex items-center justify-between bg-white rounded-lg px-4 py-2 shadow-sm">
              <span className="text-sm text-gray-700 truncate">{f.name}</span>
              <button onClick={() => removeFile(i)} className="text-red-400 hover:text-red-600 ml-2">✕</button>
            </div>
          ))}
        </div>
      )}

      {uploading && (
        <div className="mt-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Uploading...</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-indigo-600 h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {files.length > 0 && !uploading && (
        <button
          onClick={handleUpload}
          className="mt-4 w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
        >
          Upload {files.length} file{files.length > 1 ? 's' : ''}
        </button>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      {results && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="font-medium text-green-800">
            ✓ Uploaded {results.total_uploaded} file{results.total_uploaded !== 1 ? 's' : ''}
            {results.total_failed > 0 && `, ${results.total_failed} failed`}
          </p>
          {results.errors.length > 0 && (
            <ul className="mt-2 text-sm text-red-600 list-disc list-inside">
              {results.errors.map((e, i) => (
                <li key={i}>{e.file}: {e.error}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
