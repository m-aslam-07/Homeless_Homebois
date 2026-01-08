import { Vehicle } from '../App'

interface VehicleSelectorProps {
  vehicles: Vehicle[]
  selectedVehicleId: string | null
  onSelect: (vehicleId: string | null) => void
}

export default function VehicleSelector({ vehicles, selectedVehicleId, onSelect }: VehicleSelectorProps) {
  return (
    <div className="bg-white p-4 rounded-lg shadow mb-4">
      <h2 className="text-lg font-semibold mb-3">Vehicle Focus Mode</h2>
      <select
        value={selectedVehicleId || ''}
        onChange={(e) => onSelect(e.target.value || null)}
        className="w-full px-3 py-2 border border-accent rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <option value="">All Vehicles</option>
        {vehicles.map(vehicle => (
          <option key={vehicle.id} value={vehicle.id}>
            {vehicle.name} ({vehicle.current_load.toFixed(1)}/{vehicle.max_capacity.toFixed(1)} kg)
          </option>
        ))}
      </select>
      {selectedVehicleId && (
        <button
          onClick={() => onSelect(null)}
          className="mt-2 w-full text-sm text-primary hover:text-primary-dark"
        >
          Clear Selection
        </button>
      )}
    </div>
  )
}
