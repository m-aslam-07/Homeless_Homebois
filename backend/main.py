from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from contextlib import asynccontextmanager
import uvicorn
import logging
import os

# SL-3: Configure logging for observability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from database import init_db, get_db
from models import Vehicle, Shipment, ShipmentStatus
from schemas import (
    VehicleCreate, VehicleResponse,
    ShipmentCreate, ShipmentResponse,
    GeocodeRequest, GeocodeResponse,
    AllocationResponse,
    OptimizeAllocationResponse,
    RouteResponse,
    ManualAssignRequest, ManualAssignResponse
)
from services.geocoding import geocode_address
from services.allocation import allocate_shipments, optimize_allocation
from services.routing import calculate_route, calculate_route_with_precedence, calculate_distance

@asynccontextmanager
async def lifespan(app: FastAPI):
    # SL-3: Log startup
    logger.info("🚀 LogiTech Route Planning API starting up...")
    # Startup: Initialize database
    await init_db()
    logger.info("✅ Database initialized successfully")
    logger.info("✅ Application ready to accept requests")
    yield
    # Shutdown: Cleanup if needed
    logger.info("🛑 Application shutting down...")


app = FastAPI(
    title="LogiTech Route Planning API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration - Allow ALL origins for hackathon (unbreakable)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for hackathon
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],   # Allow all headers
)


@app.get("/")
async def root():
    return {"message": "LogiTech Route Planning API", "status": "operational"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Vehicle Endpoints
# SL-1: Auth Coverage - Public endpoint by design for hackathon
# TODO: Add authentication dependency in production: dependencies=[Depends(get_current_user)]
@app.post("/vehicles", response_model=VehicleResponse)
async def create_vehicle(vehicle: VehicleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new vehicle with validation and geocoding."""
    # Additional validation: current_load <= max_capacity
    if vehicle.current_load > vehicle.max_capacity:
        raise HTTPException(
            status_code=400,
            detail="current_load cannot exceed max_capacity"
        )
    
    # Geocode current_address if provided
    latitude = vehicle.latitude
    longitude = vehicle.longitude
    current_address = vehicle.current_address
    
    if current_address:
        try:
            # Geocode the address
            geocode_result = await geocode_address(current_address)
            latitude = geocode_result.latitude
            longitude = geocode_result.longitude
            current_address = geocode_result.address  # Use normalized address from geocoder
        except Exception as e:
            # If geocoding fails, return 400 Bad Request
            raise HTTPException(
                status_code=400,
                detail=f"Geocoding failed for address '{current_address}': {str(e)}"
            )
    elif latitude is None or longitude is None:
        # If no address and no coordinates provided, use default India center
        latitude = 20.59
        longitude = 78.96
        current_address = None
    
    # Create vehicle with geocoded coordinates
    db_vehicle = Vehicle(
        name=vehicle.name,
        max_capacity=vehicle.max_capacity,
        current_load=vehicle.current_load,
        max_range=vehicle.max_range,
        current_address=current_address,
        latitude=latitude,
        longitude=longitude
    )
    db.add(db_vehicle)
    await db.commit()
    await db.refresh(db_vehicle)
    return db_vehicle


# SL-1: Auth Coverage - Public endpoint by design for hackathon
@app.get("/vehicles", response_model=list[VehicleResponse])
async def get_vehicles(db: AsyncSession = Depends(get_db)):
    """Get all vehicles."""
    result = await db.execute(select(Vehicle))
    vehicles = result.scalars().all()
    return vehicles


@app.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific vehicle by ID."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@app.delete("/vehicles/{vehicle_id}", response_model=dict)
async def delete_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a vehicle and gracefully unassign its shipments. Returns updated lists."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Unassign all shipments assigned to this vehicle
    shipments_result = await db.execute(
        select(Shipment).where(Shipment.assigned_vehicle_id == vehicle_id)
    )
    assigned_shipments = shipments_result.scalars().all()
    
    for shipment in assigned_shipments:
        shipment.assigned_vehicle_id = None
        shipment.status = ShipmentStatus.PENDING
    
    # Delete the vehicle using SQLAlchemy async delete statement
    await db.execute(delete(Vehicle).where(Vehicle.id == vehicle_id))
    await db.commit()
    
    # Return updated lists
    vehicles_result = await db.execute(select(Vehicle))
    vehicles = vehicles_result.scalars().all()
    
    shipments_result = await db.execute(select(Shipment))
    shipments = shipments_result.scalars().all()
    
    return {
        "message": f"Vehicle deleted successfully. {len(assigned_shipments)} shipments unassigned.",
        "unassigned_shipments": len(assigned_shipments),
        "vehicles": vehicles,
        "shipments": shipments
    }


# Shipment Endpoints
# SL-1: Auth Coverage - Public endpoint by design for hackathon
# TODO: Add authentication dependency in production: dependencies=[Depends(get_current_user)]
@app.post("/shipments", response_model=ShipmentResponse)
async def create_shipment(shipment: ShipmentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new shipment with India bounds validation and pickup/drop validation."""
    # Validate pickup and drop are different
    if (shipment.pickup_latitude == shipment.drop_latitude and 
        shipment.pickup_longitude == shipment.drop_longitude):
        raise HTTPException(
            status_code=400,
            detail="Pickup and drop locations cannot be the same"
        )
    
    db_shipment = Shipment(**shipment.model_dump())
    db.add(db_shipment)
    await db.commit()
    await db.refresh(db_shipment)
    return db_shipment


@app.get("/shipments", response_model=list[ShipmentResponse])
async def get_shipments(db: AsyncSession = Depends(get_db)):
    """Get all shipments."""
    result = await db.execute(select(Shipment))
    shipments = result.scalars().all()
    return shipments


@app.get("/shipments/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(shipment_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific shipment by ID."""
    result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


@app.delete("/shipments/{shipment_id}", response_model=dict)
async def delete_shipment(shipment_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a shipment. If assigned, remove it from vehicle's route logic."""
    result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # If shipment is assigned to a vehicle, update vehicle's current_load
    if shipment.assigned_vehicle_id:
        vehicle_result = await db.execute(
            select(Vehicle).where(Vehicle.id == shipment.assigned_vehicle_id)
        )
        vehicle = vehicle_result.scalar_one_or_none()
        if vehicle:
            vehicle.current_load = max(0.0, vehicle.current_load - shipment.weight)
    
    # Delete the shipment
    await db.execute(delete(Shipment).where(Shipment.id == shipment_id))
    await db.commit()
    
    # Return updated lists
    vehicles_result = await db.execute(select(Vehicle))
    vehicles = vehicles_result.scalars().all()
    
    shipments_result = await db.execute(select(Shipment))
    shipments = shipments_result.scalars().all()
    
    return {
        "message": "Shipment deleted successfully.",
        "vehicles": vehicles,
        "shipments": shipments
    }


# Geocoding Endpoint
@app.post("/geocode", response_model=GeocodeResponse)
async def geocode(request: GeocodeRequest):
    """Convert address to coordinates with India bounds validation."""
    try:
        result = await geocode_address(request.address)
        return result
    except ValueError as e:
        # SL-3: Log external API errors
        logger.warning(f"⚠️ Geocoding failed for address '{request.address}': {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ External API error during geocoding: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Geocoding failed: {str(e)}")


# Allocation Endpoint
@app.post("/allocate", response_model=AllocationResponse)
async def allocate(db: AsyncSession = Depends(get_db)):
    """Auto-allocate pending shipments to available vehicles using greedy bin packing."""
    # SL-3: Log allocation start
    logger.info("🔄 Allocation process started")
    try:
        result = await allocate_shipments(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Allocation failed: {str(e)}")


# Optimize Allocation Endpoint (Multi-Objective with TSP Precedence)
@app.post("/allocate/optimize", response_model=OptimizeAllocationResponse)
async def optimize_allocate(db: AsyncSession = Depends(get_db)):
    """Optimize allocation with TSP precedence logic: reset assignments, assign optimally, and optimize routes."""
    # SL-3: Log optimization start
    logger.info("🔄 Optimization process started")
    try:
        result = await optimize_allocation(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Optimization failed: {str(e)}")


# Manual Allocation Endpoint
@app.post("/allocations/manual", response_model=ManualAssignResponse)
async def manual_assign_shipment(
    request: ManualAssignRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually assign a specific shipment to a specific vehicle.
    Validates capacity constraints before assignment.
    """
    # Fetch shipment
    shipment_result = await db.execute(
        select(Shipment).where(Shipment.id == request.shipment_id)
    )
    shipment = shipment_result.scalar_one_or_none()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Fetch vehicle
    vehicle_result = await db.execute(
        select(Vehicle).where(Vehicle.id == request.vehicle_id)
    )
    vehicle = vehicle_result.scalar_one_or_none()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Validate capacity constraint
    if vehicle.current_load + shipment.weight > vehicle.max_capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle '{vehicle.name}' does not have capacity for this shipment. "
                   f"Available: {vehicle.max_capacity - vehicle.current_load:.1f} kg, "
                   f"Required: {shipment.weight:.1f} kg"
        )
    
    # Validate range constraint (approximate)
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
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle '{vehicle.name}' does not have sufficient range for this shipment. "
                   f"Required: {total_approx_distance:.1f} km, "
                   f"Available: {vehicle.max_range:.1f} km"
        )
    
    # If shipment was previously assigned, unassign it first
    if shipment.assigned_vehicle_id:
        old_vehicle_result = await db.execute(
            select(Vehicle).where(Vehicle.id == shipment.assigned_vehicle_id)
        )
        old_vehicle = old_vehicle_result.scalar_one_or_none()
        if old_vehicle:
            old_vehicle.current_load = max(0.0, old_vehicle.current_load - shipment.weight)
    
    # Assign shipment to vehicle
    shipment.assigned_vehicle_id = vehicle.id
    shipment.status = ShipmentStatus.ASSIGNED
    vehicle.current_load += shipment.weight
    
    await db.commit()
    await db.refresh(shipment)
    await db.refresh(vehicle)
    
    logger.info(f"✅ Manual assignment: Shipment {shipment.id} → Vehicle {vehicle.name}")
    
    return ManualAssignResponse(
        message=f"Shipment assigned to {vehicle.name} successfully",
        shipment=ShipmentResponse.model_validate(shipment),
        vehicle=VehicleResponse.model_validate(vehicle)
    )


# Route Optimization Endpoint
@app.get("/vehicles/{vehicle_id}/route", response_model=RouteResponse)
async def get_vehicle_route(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    """Get optimized route for a vehicle using TSP with Precedence (Pickup before Drop)."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    try:
        # Use TSP with precedence constraint
        route = await calculate_route_with_precedence(db, vehicle_id)
        return route
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Route calculation failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
