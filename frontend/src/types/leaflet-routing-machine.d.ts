// Type definitions for leaflet-routing-machine
declare module 'leaflet-routing-machine' {
  import * as L from 'leaflet'

  namespace L {
    namespace Routing {
      interface Waypoint {
        latLng: L.LatLng
        name?: string
        options?: any
      }

      interface LineOptions {
        styles?: Array<{
          color?: string
          weight?: number
          opacity?: number
        }>
        extendToWaypoints?: boolean
        missingRouteTolerance?: number
      }

      interface RoutingControlOptions {
        waypoints: Waypoint[] | L.LatLng[]
        router?: any
        plan?: any
        geocoder?: any
        lineOptions?: LineOptions
        showAlternatives?: boolean
        addWaypoints?: boolean
        routeWhileDragging?: boolean
        reverseWaypoints?: boolean
        fitSelectedRoutes?: boolean
        show?: boolean
        createMarker?: (waypointIndex: number, waypoint: Waypoint, numberOfWaypoints: number) => L.Marker | null
        waypointMode?: string
        useZoomParameter?: boolean
        routeDragInterval?: number
      }

      class Control extends L.Control {
        constructor(options?: RoutingControlOptions)
        on(event: string, handler: (e: any) => void): this
        getWaypoints(): Waypoint[]
        setWaypoints(waypoints: Waypoint[] | L.LatLng[]): this
        spliceWaypoints(index: number, waypointsToRemove: number, ...waypointsToAdd: Waypoint[]): Waypoint[]
        getPlan(): any
        getRouter(): any
      }

      namespace osrmv1 {
        interface Options {
          serviceUrl?: string
          profile?: string
          timeout?: number
        }
      }

      function osrmv1(options?: osrmv1.Options): any
    }
  }

  export = L
}
