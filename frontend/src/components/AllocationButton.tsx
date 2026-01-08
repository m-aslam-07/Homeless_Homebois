import { useState } from 'react'
import { optimizeAllocation } from '../services/api'

interface AllocationButtonProps {
  onAllocate: () => void
  onToast: (message: string, type: 'success' | 'error') => void
  compact?: boolean
}

export default function AllocationButton({ onAllocate, onToast, compact = false }: AllocationButtonProps) {
  const [loading, setLoading] = useState(false)

  const handleOptimize = async () => {
    setLoading(true)

    try {
      const response = await optimizeAllocation()
      onToast(`Allocated ${response.allocated} shipments efficiently. ${response.unassigned} unassigned.`, 'success')
      onAllocate() // Refresh data
    } catch (err: any) {
      onToast(err.response?.data?.detail || err.message || 'Optimization failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Compact mode for header
  if (compact) {
    return (
      <button
        onClick={handleOptimize}
        disabled={loading}
        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-md transition-colors flex items-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>Allocating...</span>
          </>
        ) : (
          <>
            <span>⚡</span>
            <span>Auto-Allocate</span>
          </>
        )}
      </button>
    )
  }

  // Full card mode for sidebar
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h2 className="text-lg font-semibold mb-3">Smart Allocation</h2>
      <button
        onClick={handleOptimize}
        disabled={loading}
        className="w-full bg-primary text-white py-3 px-4 rounded-md hover:bg-primary-dark disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center font-semibold shadow-md transition-all"
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            Calculating optimal routes...
          </>
        ) : (
          <>
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Auto-Allocate & Optimize
          </>
        )}
      </button>
    </div>
  )
}
