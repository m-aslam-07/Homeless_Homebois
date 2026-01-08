from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Vehicle, Shipment, ShipmentStatus
from schemas import AllocationResponse, OptimizeAllocationResponse
from services.routing import calculate_distance


async def allocate_shipments(db: AsyncSession) -> AllocationResponse:
    """
    Load Balancing Allocation Algorithm:
    - Iterates through PENDING shipments (sorted by weight descending)
    - For each shipment, finds ALL vehicles that have enough capacity and range
    - Selection Criteria: Assigns to vehicle closest to pickup location OR least loaded
    - Ensures shipments are distributed across all vehicles rather than overloading one
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
    
    # Sort shipments by weight (descending) - heaviest first (priority)
    sorted_shipments = sorted(pending_shipments, key=lambda s: s.weight, reverse=True)
    
    assigned_count = 0
    failed_count = 0
    
    for shipment in sorted_shipments:
        # Find ALL vehicles that can take this shipment
        eligible_vehicles = []
        
        for vehicle in vehicles:
            # Check capacity constraint
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
            if total_approx_distance <= vehicle.max_range * 1.2:
                eligible_vehicles.append({
                    'vehicle': vehicle,
                    'distance_to_pickup': dist_vehicle_pickup,
                    'current_load': vehicle.current_load
                })
        
        if not eligible_vehicles:
            # No vehicle can take this shipment
            failed_count += 1
            continue
        
        # Selection Criteria: Choose vehicle that is closest to pickup OR least loaded
        # Strategy: Prioritize distance, but if distances are similar (within 10%), choose least loaded
        best_vehicle_info = None
        min_distance = float('inf')
        min_load = float('inf')
        
        for vehicle_info in eligible_vehicles:
            # Find the minimum distance
            if vehicle_info['distance_to_pickup'] < min_distance:
                min_distance = vehicle_info['distance_to_pickup']
        
        # If multiple vehicles have similar distances (within 10% of minimum), prefer least loaded
        distance_threshold = min_distance * 1.1
        
        for vehicle_info in eligible_vehicles:
            if vehicle_info['distance_to_pickup'] <= distance_threshold:
                if vehicle_info['current_load'] < min_load:
                    min_load = vehicle_info['current_load']
                    best_vehicle_info = vehicle_info
        
        # Assign shipment to best vehicle
        if best_vehicle_info:
            vehicle = best_vehicle_info['vehicle']
            shipment.assigned_vehicle_id = vehicle.id
            shipment.status = ShipmentStatus.ASSIGNED
            vehicle.current_load += shipment.weight
            
            assigned_count += 1
        else:
            failed_count += 1
    
    await db.commit()
    
    return AllocationResponse(
        assigned=assigned_count,
        failed=failed_count,
        message=f"Allocated {assigned_count} shipments, {failed_count} failed"
    )


async def optimize_allocation(db: AsyncSession) -> OptimizeAllocationResponse:
    """
    Multi-Objective Optimization:
    1. Reset: Unassign all currently pending/assigned shipments
    2. Assignment: Bin Packing with Priority/Weight sorting
    3. Routing: TSP with Precedence (Pickup before Drop) for each vehicle
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
        
        # Step 3: Bin Packing - Sort by weight (descending) for best fit
        sorted_shipments = sorted(pending_shipments, key=lambda s: s.weight, reverse=True)
        sorted_vehicles = sorted(vehicles, key=lambda v: v.max_capacity, reverse=True)
        
        allocated_count = 0
        vehicles_used = set()
        
        # Assign shipments to vehicles
        for shipment in sorted_shipments:
            assigned = False
            
            # Try to find best fit vehicle (checking capacity and range)
            for vehicle in sorted_vehicles:
                # Check capacity constraint
                if vehicle.current_load + shipment.weight <= vehicle.max_capacity:
                    # Check range constraint (approximate: distance from vehicle to pickup + pickup to drop)
                    # Calculate approximate distance: vehicle -> pickup -> drop
                    dist_vehicle_pickup = calculate_distance(
                        vehicle.latitude, vehicle.longitude,
                        shipment.pickup_latitude, shipment.pickup_longitude
                    )
                    dist_pickup_drop = calculate_distance(
                        shipment.pickup_latitude, shipment.pickup_longitude,
                        shipment.drop_latitude, shipment.drop_longitude
                    )
                    total_approx_distance = dist_vehicle_pickup + dist_pickup_drop
                    
                    # Check if within range (allow some buffer)
                    if total_approx_distance <= vehicle.max_range * 1.2:  # 20% buffer for TSP routing
                        # Assign shipment to vehicle
                        shipment.assigned_vehicle_id = vehicle.id
                        shipment.status = ShipmentStatus.ASSIGNED
                        vehicle.current_load += shipment.weight
                        vehicles_used.add(vehicle.id)
                        
                        assigned = True
                        allocated_count += 1
                        break
            
            if not assigned:
                # Cannot assign this shipment
                pass
        
        await db.commit()
        
        # Note: Routes are optimized on-demand when requested via /vehicles/{id}/route
        # using TSP with precedence logic (Pickup before Drop)
        
        unassigned_count = len(pending_shipments) - allocated_count
        
        return OptimizeAllocationResponse(
            allocated=allocated_count,
            unassigned=unassigned_count,
            vehicles_used=len(vehicles_used),
            message=f"Optimized allocation: {allocated_count} allocated, {unassigned_count} unassigned, {len(vehicles_used)} vehicles used"
        )
    
    except Exception as e:
        # Rollback on error
        await db.rollback()
        raise Exception(f"Optimization failed: {str(e)}")
