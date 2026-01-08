import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
// @ts-ignore - leaflet-routing-machine doesn't have perfect TypeScript support
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css'
// @ts-ignore
import 'leaflet-routing-machine'

interface RouteGuardProps {
  route: number[][] | null
  fallbackToPolyline: boolean
  onRouteError?: () => void
}

/**
 * RouteGuard Component
 * 
 * Attempts to display real road routes using OSRM (Open Source Routing Machine).
 * Falls back to straight-line polyline if routing fails.
 * 
 * Features:
 * - Uses OSRM demo server for road routing
 * - Graceful fallback to polyline on error
 * - Hides routing instructions panel
 * - Handles rate limiting and timeouts
 */
export default function RouteGuard({ route, fallbackToPolyline, onRouteError }: RouteGuardProps) {
  const map = useMap()
  const routingControlRef = useRef<any>(null)

  useEffect(() => {
    // Cleanup previous routing control
    if (routingControlRef.current) {
      map.removeControl(routingControlRef.current)
      routingControlRef.current = null
    }

    // If no route or route has less than 2 points, don't render anything
    if (!route || route.length < 2) {
      return
    }

    // If fallback is explicitly requested, skip routing attempt
    if (fallbackToPolyline) {
      return
    }

    // Attempt to create routing control
    try {
      // Convert route coordinates to LatLng waypoints
      const waypoints = route.map(([lat, lng]) => L.latLng(lat, lng))

      // Create routing control with OSRM
      // @ts-ignore - Type definitions may not be perfect
      const Routing = (L as any).Routing
      if (!Routing) {
        throw new Error('Leaflet Routing Machine not loaded')
      }
      
      const routingControl = Routing.control({
        waypoints: waypoints,
        router: Routing.osrmv1({
          serviceUrl: 'https://router.project-osrm.org/route/v1',
          profile: 'driving',
          timeout: 5000, // 5 second timeout
        }),
        lineOptions: {
          styles: [
            {
              color: '#2563eb', // Blue color
              weight: 5,
              opacity: 0.8,
            },
          ],
        },
        showAlternatives: false,
        addWaypoints: false, // Read-only mode
        routeWhileDragging: false,
        fitSelectedRoutes: false,
        show: false, // Hide the routing instructions panel
        createMarker: () => null, // Don't create default markers
      })

      // Add routing control to map
      routingControl.addTo(map)

      // Handle routing errors
      routingControl.on('routingerror', (e: any) => {
        console.warn('Routing error:', e.error)
        if (onRouteError) {
          onRouteError()
        }
        // Remove failed routing control
        if (routingControlRef.current) {
          map.removeControl(routingControlRef.current)
          routingControlRef.current = null
        }
      })

      // Handle successful routing
      routingControl.on('routesfound', () => {
        // Route found successfully, no action needed
      })

      // Set timeout fallback (if routing takes too long)
      const timeoutId = setTimeout(() => {
        if (routingControlRef.current) {
          console.warn('Routing timeout, falling back to polyline')
          if (onRouteError) {
            onRouteError()
          }
          map.removeControl(routingControlRef.current)
          routingControlRef.current = null
        }
      }, 8000) // 8 second timeout

      routingControlRef.current = routingControl

      // Cleanup timeout on success
      routingControl.on('routesfound', () => {
        clearTimeout(timeoutId)
      })

      // Cleanup function
      return () => {
        clearTimeout(timeoutId)
        if (routingControlRef.current) {
          map.removeControl(routingControlRef.current)
          routingControlRef.current = null
        }
      }
    } catch (error) {
      // If routing control creation fails, use polyline
      console.warn('Failed to create routing control:', error)
      if (onRouteError) {
        onRouteError()
      }
    }
  }, [route, map, fallbackToPolyline, onRouteError])

  // Hide routing instructions panel with CSS
  useEffect(() => {
    const style = document.createElement('style')
    style.textContent = `
      .leaflet-routing-container {
        display: none !important;
      }
      .leaflet-routing-alt {
        display: none !important;
      }
    `
    document.head.appendChild(style)

    return () => {
      document.head.removeChild(style)
    }
  }, [])

  // Return null - this component doesn't render anything visible
  // It only manages the routing control
  return null
}
