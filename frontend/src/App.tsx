import { useState, useEffect } from 'react'
import MapView from './components/MapView'
import ShipmentForm from './components/ShipmentForm'
import VehicleForm from './components/VehicleForm'
import AllocationButton from './components/AllocationButton'
import VehicleSelector from './components/VehicleSelector'
import ManagementConsole from './components/ManagementConsole'
import Toast from './components/Toast'
import { fetchVehicles, fetchShipments } from './services/api'

export interface Vehicle {
  id: string
  name: string
  max_capacity: number
  current_load: number
  max_range: number
  current_address: string | null
  latitude: number
  longitude: number
}

export interface Shipment {
  id: string
  pickup_address: string
  pickup_latitude: number
  pickup_longitude: number
  drop_address: string
  drop_latitude: number
  drop_longitude: number
  weight: number
  status: 'PENDING' | 'ASSIGNED' | 'DELIVERED'
  assigned_vehicle_id: string | null
}

function App() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [shipments, setShipments] = useState<Shipment[]>([])
  const [selectedVehicleId, setSelectedVehicleId] = useState<string | null>(null)
  const [selectedShipmentId, setSelectedShipmentId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [vehiclesData, shipmentsData] = await Promise.all([
        fetchVehicles(),
        fetchShipments()
      ])
      setVehicles(vehiclesData)
      setShipments(shipmentsData)
    } catch (error) {
      console.error('Failed to load data:', error)
      showToast('Failed to load data', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleDataChange = async () => {
    // Refresh data after deletion
    await loadData()
  }

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type })
  }

  useEffect(() => {
    loadData()
  }, [])

  return (
    <div className="h-screen flex flex-col">
      <header className="h-20 bg-primary text-white shadow-lg px-6 py-4 pr-6">
        <div className="flex items-center justify-between h-full">
          <div>
            <h1 className="text-lg font-bold">Route Planning & Resource Allocation</h1>
            <p className="text-xs text-white/90">India-Only Operations | Production-Grade System</p>
          </div>
          <div className="flex items-center gap-4">
            <AllocationButton onAllocate={loadData} onToast={showToast} compact={true} />
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside className="w-80 bg-background p-4 overflow-y-auto border-r border-accent">
          <div className="space-y-4">
            <VehicleSelector
              vehicles={vehicles}
              selectedVehicleId={selectedVehicleId}
              onSelect={setSelectedVehicleId}
            />
            
            <VehicleForm onVehicleCreated={loadData} />
            
            <ShipmentForm onShipmentCreated={loadData} />
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Map Area */}
          <div className="flex-1 relative">
            {loading ? (
              <div className="absolute inset-0 flex items-center justify-center bg-background z-50">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                  <p className="mt-4 text-gray-600">Loading...</p>
                </div>
              </div>
            ) : (
              <MapView
                vehicles={vehicles}
                shipments={shipments}
                selectedVehicleId={selectedVehicleId}
                selectedShipmentId={selectedShipmentId}
              />
            )}
          </div>

          {/* Management Console */}
          <div className="h-64 border-t border-gray-200 bg-white overflow-hidden flex flex-col">
            <ManagementConsole
              vehicles={vehicles}
              shipments={shipments}
              onDataChange={handleDataChange}
              onToast={showToast}
              onVehiclesUpdate={setVehicles}
              onShipmentsUpdate={setShipments}
              selectedVehicleId={selectedVehicleId}
              onVehicleSelect={setSelectedVehicleId}
              selectedShipmentId={selectedShipmentId}
              onShipmentSelect={setSelectedShipmentId}
            />
          </div>
        </main>
      </div>

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}

export default App
