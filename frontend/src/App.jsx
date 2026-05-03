import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import UploadPage from './pages/UploadPage'
import DocumentsPage from './pages/DocumentsPage'
import SummarizePage from './pages/SummarizePage'
import QueryPage from './pages/QueryPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<UploadPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="summarize" element={<SummarizePage />} />
          <Route path="query" element={<QueryPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
