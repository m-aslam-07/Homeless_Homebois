import { useState } from 'react'
import { createShipment, geocodeAddress } from '../services/api'

interface ShipmentFormProps {
  onShipmentCreated: () => void
}

export default function ShipmentForm({ onShipmentCreated }: ShipmentFormProps) {
  const [pickupAddress, setPickupAddress] = useState('')
  const [dropAddress, setDropAddress] = useState('')
  const [weight, setWeight] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingPickup, setLoadingPickup] = useState(false)
  const [loadingDrop, setLoadingDrop] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    setLoadingPickup(true)
    setLoadingDrop(true)

    try {
      // Geocode both addresses in parallel
      const [pickupResult, dropResult] = await Promise.all([
        geocodeAddress(pickupAddress).catch(err => {
          setLoadingPickup(false)
          const errorMsg = err.response?.data?.detail || err.message || 'Network error'
          throw new Error(`Pickup location error: ${errorMsg}`)
        }),
        geocodeAddress(dropAddress).catch(err => {
          setLoadingDrop(false)
          const errorMsg = err.response?.data?.detail || err.message || 'Network error'
          throw new Error(`Drop location error: ${errorMsg}`)
        })
      ])

      setLoadingPickup(false)
      setLoadingDrop(false)

      // Validate pickup and drop are different
      if (pickupResult.latitude === dropResult.latitude && 
          pickupResult.longitude === dropResult.longitude) {
        throw new Error('Pickup and drop locations cannot be the same')
      }
      
      // Create the shipment with both geocoded coordinates
      await createShipment({
        pickup_address: pickupResult.address,
        pickup_latitude: pickupResult.latitude,
        pickup_longitude: pickupResult.longitude,
        drop_address: dropResult.address,
        drop_latitude: dropResult.latitude,
        drop_longitude: dropResult.longitude,
        weight: parseFloat(weight),
      })

      // Reset form
      setPickupAddress('')
      setDropAddress('')
      setWeight('')
      onShipmentCreated()
    } catch (err: any) {
      // Better error message extraction
      let errorMessage = 'Failed to create shipment'
      if (err.message) {
        errorMessage = err.message
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message
      } else if (typeof err === 'string') {
        errorMessage = err
      }
      setError(errorMessage)
      console.error('Shipment creation error:', err)
    } finally {
      setLoading(false)
      setLoadingPickup(false)
      setLoadingDrop(false)
    }
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h2 className="text-lg font-semibold mb-3">Add Shipment</h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pickup Address <span className="text-secondary">(Source)</span>
          </label>
          <div className="relative">
            <input
              type="text"
              value={pickupAddress}
              onChange={(e) => setPickupAddress(e.target.value)}
              required
              disabled={loading}
              className="w-full px-3 py-2 border border-accent rounded-md focus:outline-none focus:ring-2 focus:ring-secondary disabled:bg-gray-100"
              placeholder="Enter pickup address in India"
            />
            {loadingPickup && (
              <div className="absolute right-3 top-2.5">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-secondary"></div>
              </div>
            )}
          </div>
          {loadingPickup && (
            <p className="text-xs text-secondary mt-1">Locating Pickup...</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Drop Address <span className="text-red-600">(Destination)</span>
          </label>
          <div className="relative">
            <input
              type="text"
              value={dropAddress}
              onChange={(e) => setDropAddress(e.target.value)}
              required
              disabled={loading}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 disabled:bg-gray-100"
              placeholder="Enter drop address in India"
            />
            {loadingDrop && (
              <div className="absolute right-3 top-2.5">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
              </div>
            )}
          </div>
          {loadingDrop && (
            <p className="text-xs text-red-600 mt-1">Locating Drop...</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Weight (kg)
          </label>
          <input
            type="number"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            required
            min="0.1"
            step="0.1"
            disabled={loading}
            className="w-full px-3 py-2 border border-accent rounded-md focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-gray-100"
            placeholder="0.0"
          />
        </div>
        {error && (
          <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={loading || loadingPickup || loadingDrop}
          className="w-full bg-primary text-white py-2 px-4 rounded-md hover:bg-primary-dark disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {loadingPickup ? 'Locating Pickup...' : loadingDrop ? 'Locating Drop...' : 'Creating...'}
            </>
          ) : (
            'Add Shipment'
          )}
        </button>
      </form>
    </div>
  )
}
