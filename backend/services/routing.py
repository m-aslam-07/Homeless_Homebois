from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from haversine import haversine, Unit
from models import Vehicle, Shipment, ShipmentStatus
from schemas import RouteResponse


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using haversine formula."""
    return haversine((lat1, lon1), (lat2, lon2), unit=Unit.KILOMETERS)


async def calculate_route_with_precedence(db: AsyncSession, vehicle_id: str) -> RouteResponse:
    """
    TSP with Precedence Constraint: Must visit Pickup before Drop.
    Uses Nearest Neighbor heuristic: From current point, find nearest valid next stop.
    Valid stop = unvisited Pickup, OR Drop for an already-picked-up shipment.
    """
    # Get vehicle
    vehicle_result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = vehicle_result.scalar_one_or_none()
    
    if not vehicle:
        raise ValueError("Vehicle not found")
    
    # Get all assigned shipments for this vehicle
    shipments_result = await db.execute(
        select(Shipment).where(
            Shipment.assigned_vehicle_id == vehicle_id,
            Shipment.status == ShipmentStatus.ASSIGNED
        )
    )
    shipments = shipments_result.scalars().all()
    
    if not shipments:
        # Return route with just vehicle location
        return RouteResponse(
            vehicle_id=vehicle_id,
            route=[[vehicle.latitude, vehicle.longitude]],
            total_distance=0.0
        )
    
    # Start at vehicle location
    route = [[vehicle.latitude, vehicle.longitude]]
    picked_up_shipments = set()  # Shipments that have been picked up
    visited_drops = set()  # Drops that have been visited
    current_lat = vehicle.latitude
    current_lon = vehicle.longitude
    total_distance = 0.0
    
    # TSP with Precedence: Continue until all drops are visited
    while len(visited_drops) < len(shipments):
        nearest_stop = None
        nearest_distance = float('inf')
        nearest_type = None  # 'pickup' or 'drop'
        nearest_shipment = None
        
        # Find nearest valid next stop
        for shipment in shipments:
            # Check if pickup is valid (not yet picked up)
            if shipment.id not in picked_up_shipments:
                pickup_distance = calculate_distance(
                    current_lat, current_lon,
                    shipment.pickup_latitude, shipment.pickup_longitude
                )
                
                if pickup_distance < nearest_distance:
                    nearest_distance = pickup_distance
                    nearest_stop = [shipment.pickup_latitude, shipment.pickup_longitude]
                    nearest_type = 'pickup'
                    nearest_shipment = shipment
            
            # Check if drop is valid (picked up but not dropped)
            if shipment.id in picked_up_shipments and shipment.id not in visited_drops:
                drop_distance = calculate_distance(
                    current_lat, current_lon,
                    shipment.drop_latitude, shipment.drop_longitude
                )
                
                if drop_distance < nearest_distance:
                    nearest_distance = drop_distance
                    nearest_stop = [shipment.drop_latitude, shipment.drop_longitude]
                    nearest_type = 'drop'
                    nearest_shipment = shipment
        
        # Visit the nearest valid stop
        if nearest_stop and nearest_shipment:
            route.append(nearest_stop)
            total_distance += nearest_distance
            current_lat = nearest_stop[0]
            current_lon = nearest_stop[1]
            
            if nearest_type == 'pickup':
                picked_up_shipments.add(nearest_shipment.id)
            elif nearest_type == 'drop':
                visited_drops.add(nearest_shipment.id)
        else:
            # Should not happen, but break to avoid infinite loop
            break
    
    return RouteResponse(
        vehicle_id=vehicle_id,
        route=route,
        total_distance=round(total_distance, 2)
    )


async def calculate_route(db: AsyncSession, vehicle_id: str) -> RouteResponse:
    """
    TSP Nearest Neighbor Algorithm for route optimization with Point-to-Point delivery.
    Starts at vehicle location, visits pickup locations, then drop locations.
    Route flows: Vehicle -> Pickup -> Drop (for each shipment).
    """
    # Get vehicle
    vehicle_result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = vehicle_result.scalar_one_or_none()
    
    if not vehicle:
        raise ValueError("Vehicle not found")
    
    # Get all assigned shipments for this vehicle
    shipments_result = await db.execute(
        select(Shipment).where(
            Shipment.assigned_vehicle_id == vehicle_id,
            Shipment.status == ShipmentStatus.ASSIGNED
        )
    )
    shipments = shipments_result.scalars().all()
    
    if not shipments:
        # Return route with just vehicle location
        return RouteResponse(
            vehicle_id=vehicle_id,
            route=[[vehicle.latitude, vehicle.longitude]],
            total_distance=0.0
        )
    
    # Start at vehicle location
    route = [[vehicle.latitude, vehicle.longitude]]
    visited_pickups = set()
    visited_drops = set()
    current_lat = vehicle.latitude
    current_lon = vehicle.longitude
    total_distance = 0.0
    
    # Nearest Neighbor Algorithm for Point-to-Point delivery
    # Strategy: Always go to nearest pickup first, then its corresponding drop
    while len(visited_pickups) < len(shipments):
        nearest_pickup = None
        nearest_pickup_distance = float('inf')
        nearest_pickup_shipment = None
        
        # Find nearest unvisited pickup
        for shipment in shipments:
            if shipment.id in visited_pickups:
                continue
            
            distance = calculate_distance(
                current_lat, current_lon,
                shipment.pickup_latitude, shipment.pickup_longitude
            )
            
            if distance < nearest_pickup_distance:
                nearest_pickup_distance = distance
                nearest_pickup = [shipment.pickup_latitude, shipment.pickup_longitude]
                nearest_pickup_shipment = shipment
        
        if nearest_pickup_shipment:
            # Add pickup to route
            route.append(nearest_pickup)
            visited_pickups.add(nearest_pickup_shipment.id)
            total_distance += nearest_pickup_distance
            current_lat = nearest_pickup_shipment.pickup_latitude
            current_lon = nearest_pickup_shipment.pickup_longitude
            
            # Immediately go to corresponding drop location
            drop_distance = calculate_distance(
                current_lat, current_lon,
                nearest_pickup_shipment.drop_latitude, nearest_pickup_shipment.drop_longitude
            )
            route.append([nearest_pickup_shipment.drop_latitude, nearest_pickup_shipment.drop_longitude])
            visited_drops.add(nearest_pickup_shipment.id)
            total_distance += drop_distance
            current_lat = nearest_pickup_shipment.drop_latitude
            current_lon = nearest_pickup_shipment.drop_longitude
    
    return RouteResponse(
        vehicle_id=vehicle_id,
        route=route,
        total_distance=round(total_distance, 2)
    )
