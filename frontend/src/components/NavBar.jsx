import React from 'react'
import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Upload' },
  { to: '/documents', label: 'Documents' },
  { to: '/summarize', label: 'Summarize' },
  { to: '/query', label: 'Query' },
]

export default function NavBar() {
  return (
    <nav className="bg-indigo-700 shadow-lg">
      <div className="max-w-6xl mx-auto px-4 flex items-center justify-between h-16">
        <span className="text-white font-bold text-xl tracking-tight">DocuRAG</span>
        <div className="flex gap-2">
          {links.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-900 text-white'
                    : 'text-indigo-100 hover:bg-indigo-600'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
