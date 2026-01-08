import { useState } from 'react'
import { createVehicle } from '../services/api'

interface VehicleFormProps {
  onVehicleCreated: () => void
}

export default function VehicleForm({ onVehicleCreated }: VehicleFormProps) {
  const [name, setName] = useState('')
  const [maxCapacity, setMaxCapacity] = useState('')
  const [maxRange, setMaxRange] = useState('')
  const [currentAddress, setCurrentAddress] = useState('')
  const [loading, setLoading] = useState(false)
  const [geocoding, setGeocoding] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    setGeocoding(!!currentAddress) // Show geocoding spinner if address provided

    try {
      await createVehicle({
        name,
        max_capacity: parseFloat(maxCapacity),
        current_load: 0,
        max_range: parseFloat(maxRange),
        current_address: currentAddress || null,
        latitude: null, // Will be geocoded from address
        longitude: null, // Will be geocoded from address
      })

      // Reset form
      setName('')
      setMaxCapacity('')
      setMaxRange('')
      setCurrentAddress('')
      onVehicleCreated()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create vehicle')
    } finally {
      setLoading(false)
      setGeocoding(false)
    }
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h2 className="text-lg font-semibold mb-3">Add Vehicle</h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full px-3 py-2 border border-accent rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Vehicle name"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Max Capacity (kg)
          </label>
          <input
            type="number"
            value={maxCapacity}
            onChange={(e) => setMaxCapacity(e.target.value)}
            required
            min="0.1"
            step="0.1"
            className="w-full px-3 py-2 border border-accent rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="0.0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Max Range (km)
          </label>
          <input
            type="number"
            value={maxRange}
            onChange={(e) => setMaxRange(e.target.value)}
            required
            min="1"
            step="1"
            className="w-full px-3 py-2 border border-accent rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Starting Location <span className="text-gray-500">(e.g., "Chennai Depot")</span>
          </label>
          <div className="relative">
            <input
              type="text"
              value={currentAddress}
              onChange={(e) => setCurrentAddress(e.target.value)}
              className="w-full px-3 py-2 border border-accent rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Enter address (optional)"
            />
            {geocoding && (
              <div className="absolute right-3 top-2.5">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              </div>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Address will be geocoded and validated for India bounds
          </p>
        </div>
        {error && (
          <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={loading || geocoding}
          className="w-full bg-secondary text-white py-2 px-4 rounded-md hover:bg-secondary-dark disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {loading ? (
            geocoding ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Geocoding address...
              </>
            ) : (
              'Creating...'
            )
          ) : (
            'Add Vehicle'
          )}
        </button>
      </form>
    </div>
  )
}
