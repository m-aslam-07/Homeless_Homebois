import { useState } from 'react'
import { Vehicle } from '../App'
import { manualAssignShipment } from '../services/api'

interface ManualAssignModalProps {
  shipmentId: string
  shipmentWeight: number
  vehicles: Vehicle[]
  onClose: () => void
  onSuccess: () => void
  onToast: (message: string, type: 'success' | 'error') => void
}

export default function ManualAssignModal({
  shipmentId,
  shipmentWeight,
  vehicles,
  onClose,
  onSuccess,
  onToast
}: ManualAssignModalProps) {
  const [selectedVehicleId, setSelectedVehicleId] = useState<string>('')
  const [loading, setLoading] = useState(false)

  // Filter vehicles that have capacity for this shipment
  const availableVehicles = vehicles.filter(
    vehicle => vehicle.current_load + shipmentWeight <= vehicle.max_capacity
  )

  const handleAssign = async () => {
    if (!selectedVehicleId) {
      onToast('Please select a vehicle', 'error')
      return
    }

    setLoading(true)
    try {
      await manualAssignShipment(shipmentId, selectedVehicleId)
      onToast('Shipment assigned successfully', 'success')
      onSuccess()
      onClose()
    } catch (err: any) {
      onToast(
        err.response?.data?.detail || err.message || 'Failed to assign shipment',
        'error'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">Assign Shipment #{shipmentId.substring(0, 8)}</h2>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Vehicle
          </label>
          <select
            value={selectedVehicleId}
            onChange={(e) => setSelectedVehicleId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={loading}
          >
            <option value="">-- Choose a vehicle --</option>
            {availableVehicles.map(vehicle => {
              const availableCapacity = vehicle.max_capacity - vehicle.current_load
              return (
                <option key={vehicle.id} value={vehicle.id}>
                  {vehicle.name} - {availableCapacity.toFixed(1)} kg available
                </option>
              )
            })}
          </select>
          {availableVehicles.length === 0 && (
            <p className="text-sm text-red-600 mt-2">
              No vehicles have capacity for this shipment ({shipmentWeight.toFixed(1)} kg)
            </p>
          )}
        </div>

        <div className="mb-4 text-sm text-gray-600">
          <p>Shipment Weight: <span className="font-medium">{shipmentWeight.toFixed(1)} kg</span></p>
        </div>

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleAssign}
            disabled={loading || !selectedVehicleId || availableVehicles.length === 0}
            className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Assigning...
              </>
            ) : (
              'Confirm Assignment'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
