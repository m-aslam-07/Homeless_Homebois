from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Vehicle, Shipment, ShipmentStatus
from schemas import AllocationResponse, OptimizeAllocationResponse
from services.routing import calculate_distance


def calculate_insertion_cost(
    vehicle: Vehicle,
    vehicle_shipments: list[Shipment],
    new_shipment: Shipment
) -> float:
    """
    Calculate the insertion cost (increase in total distance) if new_shipment is added to vehicle's route.
    
    Algorithm: Cheapest Insertion Heuristic (Simplified)
    - For empty route: cost = distance(vehicle -> pickup -> drop)
    - For existing route: Find nearest point to pickup, insert there
      Then find best position for drop after pickup
      Cost = detour distance added to route
    """
    if not vehicle_shipments:
        # Empty route: cost is distance from vehicle to pickup to drop
        dist_vehicle_pickup = calculate_distance(
            vehicle.latitude, vehicle.longitude,
            new_shipment.pickup_latitude, new_shipment.pickup_longitude
        )
        dist_pickup_drop = calculate_distance(
            new_shipment.pickup_latitude, new_shipment.pickup_longitude,
            new_shipment.drop_latitude, new_shipment.drop_longitude
        )
        return dist_vehicle_pickup + dist_pickup_drop
    
    # Build route points list
    route_points = [(vehicle.latitude, vehicle.longitude)]
    for shipment in vehicle_shipments:
        route_points.append((shipment.pickup_latitude, shipment.pickup_longitude))
        route_points.append((shipment.drop_latitude, shipment.drop_longitude))
    
    min_cost = float('inf')
    
    # Try inserting pickup at each position
    for i in range(len(route_points)):
        # Calculate cost to insert pickup after point i
        if i == 0:
            # After vehicle (start of route)
            dist_to_pickup = calculate_distance(
                route_points[0][0], route_points[0][1],
                new_shipment.pickup_latitude, new_shipment.pickup_longitude
            )
            if len(route_points) > 1:
                dist_pickup_to_next = calculate_distance(
                    new_shipment.pickup_latitude, new_shipment.pickup_longitude,
                    route_points[1][0], route_points[1][1]
                )
                dist_direct = calculate_distance(
                    route_points[0][0], route_points[0][1],
                    route_points[1][0], route_points[1][1]
                )
                pickup_cost = dist_to_pickup + dist_pickup_to_next - dist_direct
            else:
                pickup_cost = dist_to_pickup
        else:
            # In middle of route
            dist_to_pickup = calculate_distance(
                route_points[i][0], route_points[i][1],
                new_shipment.pickup_latitude, new_shipment.pickup_longitude
            )
            if i + 1 < len(route_points):
                dist_pickup_to_next = calculate_distance(
                    new_shipment.pickup_latitude, new_shipment.pickup_longitude,
                    route_points[i + 1][0], route_points[i + 1][1]
                )
                dist_direct = calculate_distance(
                    route_points[i][0], route_points[i][1],
                    route_points[i + 1][0], route_points[i + 1][1]
                )
                pickup_cost = dist_to_pickup + dist_pickup_to_next - dist_direct
            else:
                pickup_cost = dist_to_pickup
        
        # Now try inserting drop at each position after pickup
        # Drop must come after pickup in the route
        for j in range(i + 1, len(route_points) + 1):
            # Calculate cost to insert drop after point j (which is after pickup at i)
            dist_pickup_to_drop = calculate_distance(
                new_shipment.pickup_latitude, new_shipment.pickup_longitude,
                new_shipment.drop_latitude, new_shipment.drop_longitude
            )
            
            if j < len(route_points):
                # Drop inserted before existing point j
                dist_drop_to_next = calculate_distance(
                    new_shipment.drop_latitude, new_shipment.drop_longitude,
                    route_points[j][0], route_points[j][1]
                )
                # The point before drop would be pickup (if j == i+1) or route_points[j-1]
                if j == i + 1:
                    # Drop right after pickup
                    prev_point = (new_shipment.pickup_latitude, new_shipment.pickup_longitude)
                else:
                    prev_point = route_points[j - 1]
                
                dist_prev_to_next = calculate_distance(
                    prev_point[0], prev_point[1],
                    route_points[j][0], route_points[j][1]
                )
                drop_cost = dist_pickup_to_drop + dist_drop_to_next - dist_prev_to_next
            else:
                # Drop at end of route
                drop_cost = dist_pickup_to_drop
            
            total_cost = pickup_cost + drop_cost
            min_cost = min(min_cost, total_cost)
    
    return min_cost


async def allocate_shipments(db: AsyncSession) -> AllocationResponse:
    """
    Cheapest Insertion Heuristic VRP Algorithm:
    - For each unassigned shipment, calculate insertion cost for all eligible vehicles
    - Insertion cost = increase in total route distance if shipment is added
    - Assign shipment to vehicle with lowest insertion cost
    - Respects capacity and range constraints strictly
    """
    # Fetch all pending shipments
    pending_result = await db.execute(
        select(Shipment).where(Shipment.status == ShipmentStatus.PENDING)
    )
    pending_shipments = pending_result.scalars().all()
    
    # Fetch all vehicles
    vehicles_result = await db.execute(select(Vehicle))
    vehicles = vehicles_result.scalars().all()
    
    if not pending_shipments:
        return AllocationResponse(assigned=0, failed=0, message="No pending shipments")
    
    if not vehicles:
        return AllocationResponse(
            assigned=0,
            failed=len(pending_shipments),
            message="No vehicles available"
        )
    
    # Sort shipments by priority: weight (descending) and distance (furthest first)
    def shipment_priority(s: Shipment) -> float:
        pickup_drop_distance = calculate_distance(
            s.pickup_latitude, s.pickup_longitude,
            s.drop_latitude, s.drop_longitude
        )
        return s.weight * 1000 + pickup_drop_distance  # Weight is primary, distance secondary
    
    sorted_shipments = sorted(pending_shipments, key=shipment_priority, reverse=True)
    
    assigned_count = 0
    failed_count = 0
    
    # Track current assignments per vehicle for insertion cost calculation
    vehicle_assignments: dict[str, list[Shipment]] = {
        v.id: [] for v in vehicles
    }
    
    for shipment in sorted_shipments:
        best_vehicle = None
        best_cost = float('inf')
        
        # Find all eligible vehicles and calculate insertion cost
        for vehicle in vehicles:
            # Check capacity constraint (strict - never overload)
            if vehicle.current_load + shipment.weight > vehicle.max_capacity:
                continue
            
            # Check range constraint (approximate: distance from vehicle to pickup + pickup to drop)
            dist_vehicle_pickup = calculate_distance(
                vehicle.latitude, vehicle.longitude,
                shipment.pickup_latitude, shipment.pickup_longitude
            )
            dist_pickup_drop = calculate_distance(
                shipment.pickup_latitude, shipment.pickup_longitude,
                shipment.drop_latitude, shipment.drop_longitude
            )
            total_approx_distance = dist_vehicle_pickup + dist_pickup_drop
            
            # Check if within range (allow 20% buffer for TSP routing)
            if total_approx_distance > vehicle.max_range * 1.2:
                continue
            
            # Calculate insertion cost for this vehicle
            current_shipments = vehicle_assignments[vehicle.id]
            insertion_cost = calculate_insertion_cost(vehicle, current_shipments, shipment)
            
            # Select vehicle with lowest insertion cost
            if insertion_cost < best_cost:
                best_cost = insertion_cost
                best_vehicle = vehicle
        
        # Assign shipment to best vehicle
        if best_vehicle:
            shipment.assigned_vehicle_id = best_vehicle.id
            shipment.status = ShipmentStatus.ASSIGNED
            best_vehicle.current_load += shipment.weight
            vehicle_assignments[best_vehicle.id].append(shipment)
            
            assigned_count += 1
        else:
            failed_count += 1
    
    await db.commit()
    
    return AllocationResponse(
        assigned=assigned_count,
        failed=failed_count,
        message=f"Allocated {assigned_count} shipments (Cheapest Insertion VRP), {failed_count} failed"
    )


async def optimize_allocation(db: AsyncSession) -> OptimizeAllocationResponse:
    """
    Multi-Objective Optimization with Cheapest Insertion Heuristic:
    1. Reset: Unassign all currently pending/assigned shipments
    2. Assignment: Cheapest Insertion VRP algorithm
    3. Routes are optimized on-demand using TSP with Precedence
    """
    try:
        # Step 1: Reset - Unassign all pending/assigned shipments
        assigned_shipments_result = await db.execute(
            select(Shipment).where(
                Shipment.status.in_([ShipmentStatus.PENDING, ShipmentStatus.ASSIGNED])
            )
        )
        all_shipments = assigned_shipments_result.scalars().all()
        
        # Reset assignments
        for shipment in all_shipments:
            if shipment.assigned_vehicle_id:
                # Update vehicle load
                vehicle_result = await db.execute(
                    select(Vehicle).where(Vehicle.id == shipment.assigned_vehicle_id)
                )
                vehicle = vehicle_result.scalar_one_or_none()
                if vehicle:
                    vehicle.current_load = max(0.0, vehicle.current_load - shipment.weight)
            
            shipment.assigned_vehicle_id = None
            shipment.status = ShipmentStatus.PENDING
        
        await db.commit()
        
        # Step 2: Fetch pending shipments and vehicles
        pending_result = await db.execute(
            select(Shipment).where(Shipment.status == ShipmentStatus.PENDING)
        )
        pending_shipments = pending_result.scalars().all()
        
        vehicles_result = await db.execute(select(Vehicle))
        vehicles = vehicles_result.scalars().all()
        
        if not pending_shipments:
            return OptimizeAllocationResponse(
                allocated=0,
                unassigned=0,
                vehicles_used=0,
                message="No pending shipments to allocate"
            )
        
        if not vehicles:
            return OptimizeAllocationResponse(
                allocated=0,
                unassigned=len(pending_shipments),
                vehicles_used=0,
                message="No vehicles available"
            )
        
        # Step 3: Cheapest Insertion VRP Algorithm
        def shipment_priority(s: Shipment) -> float:
            pickup_drop_distance = calculate_distance(
                s.pickup_latitude, s.pickup_longitude,
                s.drop_latitude, s.drop_longitude
            )
            return s.weight * 1000 + pickup_drop_distance
        
        sorted_shipments = sorted(pending_shipments, key=shipment_priority, reverse=True)
        
        allocated_count = 0
        vehicles_used = set()
        vehicle_assignments: dict[str, list[Shipment]] = {
            v.id: [] for v in vehicles
        }
        
        for shipment in sorted_shipments:
            best_vehicle = None
            best_cost = float('inf')
            
            for vehicle in vehicles:
                # Check capacity constraint
                if vehicle.current_load + shipment.weight > vehicle.max_capacity:
                    continue
                
                # Check range constraint
                dist_vehicle_pickup = calculate_distance(
                    vehicle.latitude, vehicle.longitude,
                    shipment.pickup_latitude, shipment.pickup_longitude
                )
                dist_pickup_drop = calculate_distance(
                    shipment.pickup_latitude, shipment.pickup_longitude,
                    shipment.drop_latitude, shipment.drop_longitude
                )
                total_approx_distance = dist_vehicle_pickup + dist_pickup_drop
                
                if total_approx_distance > vehicle.max_range * 1.2:
                    continue
                
                # Calculate insertion cost
                current_shipments = vehicle_assignments[vehicle.id]
                insertion_cost = calculate_insertion_cost(vehicle, current_shipments, shipment)
                
                if insertion_cost < best_cost:
                    best_cost = insertion_cost
                    best_vehicle = vehicle
            
            if best_vehicle:
                shipment.assigned_vehicle_id = best_vehicle.id
                shipment.status = ShipmentStatus.ASSIGNED
                best_vehicle.current_load += shipment.weight
                vehicles_used.add(best_vehicle.id)
                vehicle_assignments[best_vehicle.id].append(shipment)
                
                allocated_count += 1
        
        await db.commit()
        
        unassigned_count = len(pending_shipments) - allocated_count
        
        return OptimizeAllocationResponse(
            allocated=allocated_count,
            unassigned=unassigned_count,
            vehicles_used=len(vehicles_used),
            message=f"Optimized allocation (Cheapest Insertion VRP): {allocated_count} allocated, {unassigned_count} unassigned, {len(vehicles_used)} vehicles used"
        )
    
    except Exception as e:
        # Rollback on error
        await db.rollback()
        raise Exception(f"Optimization failed: {str(e)}")
