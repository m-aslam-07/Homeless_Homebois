import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Log API URL for debugging
console.log('🔗 API Base URL:', API_BASE_URL)

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
})

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`📤 ${config.method?.toUpperCase()} ${config.url}`, config.data || '')
    return config
  },
  (error) => {
    console.error('❌ Request error:', error)
    return Promise.reject(error)
  }
)

// SL-2: Add retry logic for network errors and 503 responses
const retryConfig = {
  retries: 1,
  retryDelay: 1000, // 1 second delay
  retryCondition: (error: any) => {
    // Retry on network errors or 503 Service Unavailable
    return (
      error.code === 'ERR_NETWORK' ||
      error.message === 'Network Error' ||
      error.response?.status === 503
    )
  }
}

// Add error interceptor with retry logic
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle different types of network errors
    if (error.code === 'ECONNABORTED') {
      error.message = 'Request timeout - the server took too long to respond. Please try again.'
    } else if (error.message === 'Network Error' || error.code === 'ERR_NETWORK') {
      error.message = `Cannot connect to backend API at ${API_BASE_URL}. Please check:
1. Backend is running (http://localhost:8000/health)
2. No firewall blocking the connection
3. Backend container is up: docker ps | grep backend`
    } else if (!error.response) {
      error.message = `Network error: ${error.message || 'Unknown error'}. Backend may be unavailable.`
    } else if (error.response?.status === 503) {
      error.message = 'Service temporarily unavailable. Please try again in a moment.'
    }
    
    // SL-2: Retry logic for network errors and 503
    if (retryConfig.retryCondition(error) && error.config && !error.config.__retryCount) {
      error.config.__retryCount = (error.config.__retryCount || 0) + 1
      if (error.config.__retryCount <= retryConfig.retries) {
        await new Promise(resolve => setTimeout(resolve, retryConfig.retryDelay))
        return api.request(error.config)
      }
    }
    
    return Promise.reject(error)
  }
)

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

export interface GeocodeResponse {
  latitude: number
  longitude: number
  address: string
}

export interface AllocationResponse {
  assigned: number
  failed: number
  message: string
}

export interface RouteResponse {
  vehicle_id: string
  route: number[][]
  total_distance: number
}

export interface DeleteVehicleResponse {
  message: string
  unassigned_shipments: number
  vehicles: Vehicle[]
  shipments: Shipment[]
}

export interface DeleteShipmentResponse {
  message: string
  vehicles: Vehicle[]
  shipments: Shipment[]
}

export interface OptimizeAllocationResponse {
  allocated: number
  unassigned: number
  vehicles_used: number
  message: string
}

// Vehicle APIs
export const fetchVehicles = async (): Promise<Vehicle[]> => {
  const response = await api.get<Vehicle[]>('/vehicles')
  return response.data
}

export const createVehicle = async (vehicle: {
  name: string
  max_capacity: number
  current_load: number
  max_range: number
  current_address?: string | null
  latitude?: number | null
  longitude?: number | null
}): Promise<Vehicle> => {
  const response = await api.post<Vehicle>('/vehicles', vehicle)
  return response.data
}

export const fetchVehicle = async (id: string): Promise<Vehicle> => {
  const response = await api.get<Vehicle>(`/vehicles/${id}`)
  return response.data
}

// Shipment APIs
export const fetchShipments = async (): Promise<Shipment[]> => {
  const response = await api.get<Shipment[]>('/shipments')
  return response.data
}

export const createShipment = async (shipment: {
  pickup_address: string
  pickup_latitude: number
  pickup_longitude: number
  drop_address: string
  drop_latitude: number
  drop_longitude: number
  weight: number
}): Promise<Shipment> => {
  const response = await api.post<Shipment>('/shipments', shipment)
  return response.data
}

// Geocoding API
export const geocodeAddress = async (address: string): Promise<GeocodeResponse> => {
  const response = await api.post<GeocodeResponse>('/geocode', { address })
  return response.data
}

// Allocation API
export const allocateShipments = async (): Promise<AllocationResponse> => {
  const response = await api.post<AllocationResponse>('/allocate')
  return response.data
}

// Route API
export const fetchVehicleRoute = async (vehicleId: string): Promise<RouteResponse> => {
  const response = await api.get<RouteResponse>(`/vehicles/${vehicleId}/route`)
  return response.data
}

// Delete APIs
export const deleteVehicle = async (id: string): Promise<DeleteVehicleResponse> => {
  const response = await api.delete<DeleteVehicleResponse>(`/vehicles/${id}`)
  return response.data
}

export const deleteShipment = async (id: string): Promise<DeleteShipmentResponse> => {
  const response = await api.delete<DeleteShipmentResponse>(`/shipments/${id}`)
  return response.data
}

// Optimize Allocation API
export const optimizeAllocation = async (): Promise<OptimizeAllocationResponse> => {
  const response = await api.post<OptimizeAllocationResponse>('/allocate/optimize')
  return response.data
}

// Manual Assignment API
export interface ManualAssignRequest {
  shipment_id: string
  vehicle_id: string
}

export interface ManualAssignResponse {
  message: string
  shipment: Shipment
  vehicle: Vehicle
}

export const manualAssignShipment = async (
  shipmentId: string,
  vehicleId: string
): Promise<ManualAssignResponse> => {
  const response = await api.post<ManualAssignResponse>('/allocations/manual', {
    shipment_id: shipmentId,
    vehicle_id: vehicleId
  })
  return response.data
}
