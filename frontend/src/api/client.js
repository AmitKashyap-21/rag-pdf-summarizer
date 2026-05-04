import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''
const API_KEY = import.meta.env.VITE_API_KEY || 'changeme'

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Authorization': `Bearer ${API_KEY}`
  }
})

export const uploadDocuments = (files, onProgress) => {
  const formData = new FormData()
  files.forEach(file => formData.append('files', file))
  return client.post('/api/v1/documents/upload', formData, {
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }
  })
}

export const listDocuments = (skip = 0, limit = 10, status = '') => {
  const params = { skip, limit }
  if (status) params.status = status
  return client.get('/api/v1/documents', { params })
}

export const getDocument = (id) => client.get(`/api/v1/documents/${id}`)

export const summarizeDocument = (id, data) =>
  client.post(`/api/v1/documents/${id}/summarize`, data)

export const queryDocument = (id, data) =>
  client.post(`/api/v1/documents/${id}/query`, data)

export const deleteDocument = (id) => client.delete(`/api/v1/documents/${id}`)

export const healthCheck = () => client.get('/health')
