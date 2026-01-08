import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import { Vehicle, Shipment } from '../App'
import { fetchVehicleRoute, RouteResponse } from '../services/api'
import RouteGuard from './RouteGuard'

// Fix for default marker icons in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// Custom truck icon for vehicles
const truckIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

interface MapViewProps {
  vehicles: Vehicle[]
  shipments: Shipment[]
  selectedVehicleId: string | null
  selectedShipmentId: string | null
}

// Component to update map bounds when vehicle or shipment is selected (Focus Mode)
function MapBoundsUpdater({ 
  selectedVehicleId,
  selectedShipmentId,
  vehicles, 
  shipments, 
  route 
}: { 
  selectedVehicleId: string | null
  selectedShipmentId: string | null
  vehicles: Vehicle[]
  shipments: Shipment[]
  route: RouteResponse | null
}) {
  const map = useMap()
  
  useEffect(() => {
    // Priority: Shipment selection overrides vehicle selection
    if (selectedShipmentId) {
      const shipment = shipments.find(s => s.id === selectedShipmentId)
      if (shipment) {
        // Focus on shipment's pickup and drop locations
        const points: [number, number][] = [
          [shipment.pickup_latitude, shipment.pickup_longitude],
          [shipment.drop_latitude, shipment.drop_longitude]
        ]
        const bounds = L.latLngBounds(points)
        map.fitBounds(bounds, { padding: [100, 100], maxZoom: 10 })
      }
    } else if (selectedVehicleId) {
      const vehicle = vehicles.find(v => v.id === selectedVehicleId)
      if (vehicle) {
        // If route is available, use it for more accurate bounds
        if (route && route.route.length > 0) {
          const bounds = L.latLngBounds(route.route as [number, number][])
          map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 })
        } else {
          // Fallback: use vehicle and assigned shipments
          const assignedShipments = shipments.filter(s => s.assigned_vehicle_id === selectedVehicleId)
          const allPoints = [
            [vehicle.latitude, vehicle.longitude],
            ...assignedShipments.flatMap(s => [
              [s.pickup_latitude, s.pickup_longitude],
              [s.drop_latitude, s.drop_longitude]
            ])
          ]
          
          if (allPoints.length > 0) {
            const bounds = L.latLngBounds(allPoints as [number, number][])
            map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 })
          }
        }
      }
    } else {
      // Reset to India view when nothing selected
      map.setView([20.59, 78.96], 5)
    }
  }, [selectedVehicleId, selectedShipmentId, vehicles, shipments, route, map])
  
  return null
}

export default function MapView({ vehicles, shipments, selectedVehicleId, selectedShipmentId }: MapViewProps) {
  const [route, setRoute] = useState<RouteResponse | null>(null)
  const [loadingRoute, setLoadingRoute] = useState(false)
  const [usePolylineFallback, setUsePolylineFallback] = useState(false)

  // India bounds
  const indiaCenter: [number, number] = [20.59, 78.96]
  const indiaBounds: [[number, number], [number, number]] = [
    [6.0, 68.0],  // Southwest corner
    [38.0, 98.0]  // Northeast corner
  ]

  useEffect(() => {
    if (selectedVehicleId) {
      setLoadingRoute(true)
      setUsePolylineFallback(false) // Reset fallback state
      fetchVehicleRoute(selectedVehicleId)
        .then(setRoute)
        .catch(err => {
          console.error('Failed to fetch route:', err)
          setRoute(null)
        })
        .finally(() => setLoadingRoute(false))
    } else {
      setRoute(null)
      setUsePolylineFallback(false)
    }
  }, [selectedVehicleId])

  // Filter vehicles and shipments based on selection
  const displayVehicles = selectedVehicleId
    ? vehicles.filter(v => v.id === selectedVehicleId)
    : vehicles

  const displayShipments = selectedVehicleId
    ? shipments.filter(s => s.assigned_vehicle_id === selectedVehicleId)
    : shipments

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={indiaCenter}
        zoom={5}
        style={{ height: '100%', width: '100%' }}
        maxBounds={indiaBounds}
        maxBoundsViscosity={1.0}
        minZoom={4}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapBoundsUpdater
          selectedVehicleId={selectedVehicleId}
          selectedShipmentId={selectedShipmentId}
          vehicles={vehicles}
          shipments={shipments}
          route={route}
        />

        {/* Vehicle Markers with Truck Icon */}
        {displayVehicles.map(vehicle => (
          <Marker
            key={vehicle.id}
            position={[vehicle.latitude, vehicle.longitude]}
            icon={truckIcon}
          >
            <Popup>
              <div className="font-semibold">{vehicle.name}</div>
              {vehicle.current_address && (
                <div className="text-sm text-gray-600 mb-1">📍 {vehicle.current_address}</div>
              )}
              <div>Capacity: {vehicle.current_load.toFixed(1)} / {vehicle.max_capacity.toFixed(1)} kg</div>
              <div>Range: {vehicle.max_range} km</div>
              {selectedVehicleId === vehicle.id && (
                <div className="mt-2 text-xs bg-primary/20 text-primary-dark px-2 py-1 rounded">
                  ✨ Focus Mode Active
                </div>
              )}
            </Popup>
          </Marker>
        ))}

        {/* Numbered Route Markers - Only show when route is available */}
        {route && route.route.length > 1 && selectedVehicleId && (
          <>
            {route.route.map((point, index) => {
              // First point is vehicle location (use truck icon)
              if (index === 0) {
                return null // Vehicle already displayed above
              }

              // Find which shipment this point belongs to
              const isPickup = displayShipments.some(s => 
                Math.abs(s.pickup_latitude - point[0]) < 0.001 && 
                Math.abs(s.pickup_longitude - point[1]) < 0.001
              )
              const isDrop = displayShipments.some(s =>
                Math.abs(s.drop_latitude - point[0]) < 0.001 &&
                Math.abs(s.drop_longitude - point[1]) < 0.001
              )

              // Create numbered marker
              const markerColor = isPickup ? '#22c55e' : '#ef4444' // Green for pickup, Red for drop
              const customIcon = L.divIcon({
                className: 'custom-numbered-marker',
                html: `
                  <div style="
                    background-color: ${markerColor};
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    border: 3px solid white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                  ">${index}</div>
                `,
                iconSize: [32, 32],
                iconAnchor: [16, 16],
                popupAnchor: [0, -16],
              })

              // Find shipment for popup
              const shipment = displayShipments.find(s =>
                (isPickup && Math.abs(s.pickup_latitude - point[0]) < 0.001 && Math.abs(s.pickup_longitude - point[1]) < 0.001) ||
                (isDrop && Math.abs(s.drop_latitude - point[0]) < 0.001 && Math.abs(s.drop_longitude - point[1]) < 0.001)
              )

              return (
                <Marker key={`route-${index}`} position={point as [number, number]} icon={customIcon}>
                  <Popup>
                    <div className="font-semibold">
                      {isPickup ? (
                        <span className="text-secondary">Pickup #{index}</span>
                      ) : (
                        <span className="text-red-600">Drop #{index}</span>
                      )}
                    </div>
                    {shipment && (
                      <>
                        <div>Address: {isPickup ? shipment.pickup_address : shipment.drop_address}</div>
                        <div>Weight: {shipment.weight} kg</div>
                      </>
                    )}
                  </Popup>
                </Marker>
              )
            })}
          </>
        )}

        {/* Preview Route for Selected Shipment */}
        {selectedShipmentId && !selectedVehicleId && (() => {
          const selectedShipment = shipments.find(s => s.id === selectedShipmentId)
          if (!selectedShipment) return null
          
          // Green marker for pickup
          const pickupPreviewIcon = new L.Icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
            iconSize: [35, 50],
            iconAnchor: [17, 50],
            popupAnchor: [1, -34],
          })
          
          // Red marker for drop
          const dropPreviewIcon = new L.Icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
            iconSize: [35, 50],
            iconAnchor: [17, 50],
            popupAnchor: [1, -34],
          })
          
          return (
            <>
              {/* Pickup Marker (Green, Larger) */}
              <Marker
                position={[selectedShipment.pickup_latitude, selectedShipment.pickup_longitude]}
                icon={pickupPreviewIcon}
              >
                <Popup>
                  <div className="font-semibold text-secondary">📍 Pickup Location</div>
                  <div className="text-sm">{selectedShipment.pickup_address}</div>
                  <div className="text-sm">Weight: {selectedShipment.weight} kg</div>
                  <div className="mt-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                    ✨ Preview Route Active
                  </div>
                </Popup>
              </Marker>
              
              {/* Drop Marker (Red, Larger) */}
              <Marker
                position={[selectedShipment.drop_latitude, selectedShipment.drop_longitude]}
                icon={dropPreviewIcon}
              >
                <Popup>
                  <div className="font-semibold text-red-600">📍 Drop Location</div>
                  <div className="text-sm">{selectedShipment.drop_address}</div>
                  <div className="text-sm">Weight: {selectedShipment.weight} kg</div>
                  <div className="mt-2 text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                    ✨ Preview Route Active
                  </div>
                </Popup>
              </Marker>
              
              {/* Dotted Preview Route Line */}
              <Polyline
                positions={[
                  [selectedShipment.pickup_latitude, selectedShipment.pickup_longitude],
                  [selectedShipment.drop_latitude, selectedShipment.drop_longitude]
                ]}
                color="#3b82f6"
                weight={3}
                opacity={0.8}
                dashArray="10, 10"
              />
            </>
          )
        })()}

        {/* Fallback: Show regular markers when no route is selected */}
        {(!route || !selectedVehicleId) && !selectedShipmentId && displayShipments.map(shipment => {
          // Green marker for pickup location
          const pickupIcon = new L.Icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
          })

          // Red marker for drop location
          const dropIcon = new L.Icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
          })

          return (
            <div key={shipment.id}>
              {/* Pickup Marker (Green) */}
              <Marker
                position={[shipment.pickup_latitude, shipment.pickup_longitude]}
                icon={pickupIcon}
              >
                <Popup>
                  <div className="font-semibold text-secondary">Pickup Location</div>
                  <div>Address: {shipment.pickup_address}</div>
                  <div>Weight: {shipment.weight} kg</div>
                  <div>Status: {shipment.status}</div>
                </Popup>
              </Marker>
              
              {/* Drop Marker (Red) */}
              <Marker
                position={[shipment.drop_latitude, shipment.drop_longitude]}
                icon={dropIcon}
              >
                <Popup>
                  <div className="font-semibold text-red-600">Drop Location</div>
                  <div>Address: {shipment.drop_address}</div>
                  <div>Weight: {shipment.weight} kg</div>
                  <div>Status: {shipment.status}</div>
                </Popup>
              </Marker>
            </div>
          )
        })}

        {/* Real Road Routing (with fallback to polyline) */}
        {route && route.route.length > 1 && (
          <>
            <RouteGuard
              route={route.route}
              fallbackToPolyline={usePolylineFallback}
              onRouteError={() => setUsePolylineFallback(true)}
            />
            {/* Fallback Polyline (shown if routing fails) */}
            {usePolylineFallback && (
              <Polyline
                positions={route.route as [number, number][]}
                color="blue"
                weight={4}
                opacity={0.7}
              />
            )}
          </>
        )}
      </MapContainer>

      {loadingRoute && (
        <div className="absolute top-4 right-4 bg-white p-2 rounded shadow-lg">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
            <span className="text-sm">Calculating route...</span>
          </div>
        </div>
      )}

      {route && route.route.length > 1 && (
        <div className="absolute top-4 left-4 bg-white p-3 rounded shadow-lg">
          <div className="text-sm font-semibold">Route Information</div>
          <div className="text-xs text-gray-600">Total Distance: {route.total_distance.toFixed(2)} km</div>
          <div className="text-xs text-gray-600">Stops: {route.route.length}</div>
        </div>
      )}
    </div>
  )
}
