import { useState } from 'react'
import { Vehicle, Shipment } from '../App'
import { deleteVehicle, deleteShipment } from '../services/api'

interface ManagementConsoleProps {
  vehicles: Vehicle[]
  shipments: Shipment[]
  onDataChange: () => void
  onToast: (message: string, type: 'success' | 'error') => void
  onVehiclesUpdate: (vehicles: Vehicle[]) => void
  onShipmentsUpdate: (shipments: Shipment[]) => void
  selectedVehicleId: string | null
  onVehicleSelect: (vehicleId: string | null) => void
}

type TabType = 'vehicles' | 'shipments' | 'allocations'

export default function ManagementConsole({ 
  vehicles, 
  shipments, 
  onDataChange, 
  onToast,
  onVehiclesUpdate,
  onShipmentsUpdate,
  selectedVehicleId,
  onVehicleSelect
}: ManagementConsoleProps) {
  const [activeTab, setActiveTab] = useState<TabType>('vehicles')
  const [deleting, setDeleting] = useState<string | null>(null)

  const handleVehicleRowClick = (vehicleId: string, e: React.MouseEvent) => {
    // Don't trigger if clicking on the delete button
    if ((e.target as HTMLElement).closest('button')) {
      return
    }
    
    // Toggle focus mode
    if (selectedVehicleId === vehicleId) {
      onVehicleSelect(null) // Clear focus
    } else {
      onVehicleSelect(vehicleId) // Focus on this vehicle
    }
  }

  const handleDeleteVehicle = async (vehicleId: string, vehicleName: string) => {
    if (!window.confirm(`Are you sure you want to delete vehicle "${vehicleName}"? This will unassign all its shipments.`)) {
      return
    }

    setDeleting(vehicleId)
    try {
      const response = await deleteVehicle(vehicleId)
      // Update state immediately for instant UI update
      if (response.vehicles) {
        onVehiclesUpdate(response.vehicles)
      }
      if (response.shipments) {
        onShipmentsUpdate(response.shipments)
      }
      onToast(`Vehicle "${vehicleName}" deleted successfully. ${response.unassigned_shipments || 0} shipments unassigned.`, 'success')
      // Also refresh to ensure consistency
      onDataChange()
    } catch (error: any) {
      onToast(error.response?.data?.detail || error.message || 'Failed to delete vehicle', 'error')
    } finally {
      setDeleting(null)
    }
  }

  const handleDeleteShipment = async (shipmentId: string, pickupAddress: string) => {
    if (!window.confirm(`Are you sure you want to delete shipment from "${pickupAddress}"?`)) {
      return
    }

    setDeleting(shipmentId)
    try {
      const response = await deleteShipment(shipmentId)
      // Update state immediately for instant UI update
      if (response.vehicles) {
        onVehiclesUpdate(response.vehicles)
      }
      if (response.shipments) {
        onShipmentsUpdate(response.shipments)
      }
      onToast(`Shipment from "${pickupAddress}" deleted successfully.`, 'success')
      // Also refresh to ensure consistency
      onDataChange()
    } catch (error: any) {
      onToast(error.response?.data?.detail || error.message || 'Failed to delete shipment', 'error')
    } finally {
      setDeleting(null)
    }
  }

  // Build allocations data
  const allocations = vehicles
    .filter(v => shipments.some(s => s.assigned_vehicle_id === v.id))
    .map(vehicle => ({
      vehicle,
      shipments: shipments.filter(s => s.assigned_vehicle_id === vehicle.id)
    }))

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200 h-full flex flex-col overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-gray-200 flex-shrink-0">
        <button
          onClick={() => setActiveTab('vehicles')}
          className={`px-6 py-3 font-semibold text-sm transition-colors ${
            activeTab === 'vehicles'
              ? 'bg-accent-light text-primary border-b-2 border-primary'
              : 'text-gray-600 hover:bg-accent'
          }`}
        >
          Vehicles ({vehicles.length})
        </button>
        <button
          onClick={() => setActiveTab('shipments')}
          className={`px-6 py-3 font-semibold text-sm transition-colors ${
            activeTab === 'shipments'
              ? 'bg-accent-light text-primary border-b-2 border-primary'
              : 'text-gray-600 hover:bg-accent'
          }`}
        >
          Shipments ({shipments.length})
        </button>
        <button
          onClick={() => setActiveTab('allocations')}
          className={`px-6 py-3 font-semibold text-sm transition-colors ${
            activeTab === 'allocations'
              ? 'bg-accent-light text-primary border-b-2 border-primary'
              : 'text-gray-600 hover:bg-accent'
          }`}
        >
          Allocations ({allocations.length})
        </button>
      </div>

      {/* Tab Content */}
      <div className="p-4 flex-1 overflow-y-auto">
        {activeTab === 'vehicles' && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">ID</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">Name</th>
                  <th className="text-right py-2 px-3 font-semibold text-gray-700">Capacity</th>
                  <th className="text-right py-2 px-3 font-semibold text-gray-700">Current Load</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">Status</th>
                  <th className="text-center py-2 px-3 font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {vehicles.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-gray-500">
                      No vehicles found
                    </td>
                  </tr>
                ) : (
                  vehicles.map(vehicle => {
                    const loadPercentage = (vehicle.current_load / vehicle.max_capacity) * 100
                    const status = loadPercentage === 0 ? 'Empty' : loadPercentage >= 90 ? 'Full' : 'In Use'
                    const statusColor = status === 'Empty' ? 'text-gray-600' : status === 'Full' ? 'text-red-600' : 'text-secondary'
                    const isSelected = selectedVehicleId === vehicle.id
                    
                    return (
                      <tr 
                        key={vehicle.id} 
                        onClick={(e) => handleVehicleRowClick(vehicle.id, e)}
                        className={`border-b border-gray-100 cursor-pointer transition-colors ${
                          isSelected 
                            ? 'bg-accent-light hover:bg-accent border-l-4 border-l-primary' 
                            : 'hover:bg-accent/50'
                        }`}
                      >
                        <td className="py-2 px-3 text-gray-600 font-mono text-xs">{vehicle.id.substring(0, 8)}...</td>
                        <td className="py-2 px-3 font-medium">
                          <div className="flex items-center gap-2">
                            {vehicle.name}
                            {isSelected && (
                              <span className="text-xs bg-primary text-white px-2 py-0.5 rounded">Focused</span>
                            )}
                          </div>
                        </td>
                        <td className="py-2 px-3 text-right">{vehicle.max_capacity.toFixed(1)}</td>
                        <td className="py-2 px-3 text-right">{vehicle.current_load.toFixed(1)}</td>
                        <td className={`py-2 px-3 ${statusColor} font-medium`}>{status}</td>
                        <td className="py-2 px-3 text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteVehicle(vehicle.id, vehicle.name)
                            }}
                            disabled={deleting === vehicle.id}
                            className="text-red-600 hover:text-red-700 disabled:text-gray-400 disabled:cursor-not-allowed"
                            title="Delete vehicle"
                          >
                            {deleting === vehicle.id ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                            ) : (
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            )}
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'shipments' && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">ID</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">Source</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">Destination</th>
                  <th className="text-right py-2 px-3 font-semibold text-gray-700">Weight</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">Status</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">Assigned To</th>
                  <th className="text-center py-2 px-3 font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {shipments.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-gray-500">
                      No shipments found
                    </td>
                  </tr>
                ) : (
                  shipments.map(shipment => {
                    const assignedVehicle = shipment.assigned_vehicle_id
                      ? vehicles.find(v => v.id === shipment.assigned_vehicle_id)
                      : null
                    
                    return (
                      <tr key={shipment.id} className="border-b border-gray-100 hover:bg-accent/50">
                        <td className="py-2 px-3 text-gray-600 font-mono text-xs">{shipment.id.substring(0, 8)}...</td>
                        <td className="py-2 px-3 text-gray-700 max-w-xs truncate" title={shipment.pickup_address}>
                          {shipment.pickup_address}
                        </td>
                        <td className="py-2 px-3 text-gray-700 max-w-xs truncate" title={shipment.drop_address}>
                          {shipment.drop_address}
                        </td>
                        <td className="py-2 px-3 text-right">{shipment.weight.toFixed(1)}</td>
                        <td className="py-2 px-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            shipment.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                            shipment.status === 'ASSIGNED' ? 'bg-primary/20 text-primary-dark' :
                            'bg-secondary/20 text-secondary-dark'
                          }`}>
                            {shipment.status}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-gray-600">
                          {assignedVehicle ? assignedVehicle.name : '-'}
                        </td>
                        <td className="py-2 px-3 text-center">
                          <button
                            onClick={() => handleDeleteShipment(shipment.id, shipment.pickup_address)}
                            disabled={deleting === shipment.id}
                            className="text-red-600 hover:text-red-700 disabled:text-gray-400 disabled:cursor-not-allowed"
                            title="Delete shipment"
                          >
                            {deleting === shipment.id ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                            ) : (
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            )}
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'allocations' && (
          <div className="space-y-4">
            {allocations.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No allocations found
              </div>
            ) : (
              allocations.map(({ vehicle, shipments: vehicleShipments }) => (
                <div key={vehicle.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="font-semibold text-lg mb-2">{vehicle.name}</div>
                  <div className="text-sm text-gray-600 mb-3">
                    Load: {vehicle.current_load.toFixed(1)} / {vehicle.max_capacity.toFixed(1)} ({vehicleShipments.length} shipments)
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {vehicleShipments.map(shipment => (
                      <span
                        key={shipment.id}
                        className="px-3 py-1 bg-primary/20 text-primary-dark rounded-full text-xs font-medium"
                        title={`${shipment.pickup_address} → ${shipment.drop_address}`}
                      >
                        #{shipment.id.substring(0, 8)}...
                      </span>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
