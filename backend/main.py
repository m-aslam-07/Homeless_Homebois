from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security.api_key import APIKeyHeader
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

# --- SECURITY CONFIGURATION ---
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# Define secure keys (In production, these come from a DB or Vault)
# Hackathon tip: Set these in your Render Environment Variables
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "logitech-admin-secret-123")
USER_API_KEY = os.getenv("USER_API_KEY", "logitech-user-view-456")

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """Validates that a valid API key is present."""
    if api_key_header in [ADMIN_API_KEY, USER_API_KEY]:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials"
    )

async def verify_admin(api_key_header: str = Security(api_key_header)):
    """Role-Based Access: Only allows requests with the Admin API Key."""
    if api_key_header == ADMIN_API_KEY:
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin privileges required for this operation"
    )
# -----------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # SL-3: Log startup
    logger.info("🚀 LogiTech Route Planning API starting up...")
    await init_db()
    logger.info("✅ Database initialized successfully")
    yield
    logger.info("🛑 Application shutting down...")


app = FastAPI(
    title="LogiTech Route Planning API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
origins = [origin.strip() for origin in origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "LogiTech Route Planning API", "status": "operational"}

# Health check usually remains public for load balancers
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Vehicle Endpoints

# SECURED: Creation requires Admin privileges
@app.post("/vehicles", response_model=VehicleResponse, dependencies=[Depends(verify_admin)])
async def create_vehicle(vehicle: VehicleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new vehicle (Admin Only)."""
    if vehicle.current_load > vehicle.max_capacity:
        raise HTTPException(
            status_code=400,
            detail="current_load cannot exceed max_capacity"
        )
    
    # Geocoding logic...
    latitude = vehicle.latitude
    longitude = vehicle.longitude
    current_address = vehicle.current_address
    
    if current_address:
        try:
            geocode_result = await geocode_address(current_address)
            latitude = geocode_result.latitude
            longitude = geocode_result.longitude
            current_address = geocode_result.address
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif latitude is None or longitude is None:
        latitude = 20.59
        longitude = 78.96
        current_address = None
    
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


# SECURED: Read requires at least a valid User key
@app.get("/vehicles", response_model=list[VehicleResponse], dependencies=[Depends(get_api_key)])
async def get_vehicles(db: AsyncSession = Depends(get_db)):
    """Get all vehicles (Authenticated)."""
    result = await db.execute(select(Vehicle))
    vehicles = result.scalars().all()
    return vehicles


@app.get("/vehicles/{vehicle_id}", response_model=VehicleResponse, dependencies=[Depends(get_api_key)])
async def get_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific vehicle (Authenticated)."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


# SECURED: CRITICAL - Deletion requires strict Admin privileges
@app.delete("/vehicles/{vehicle_id}", response_model=dict, dependencies=[Depends(verify_admin)])
async def delete_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a vehicle (Admin Only)."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Unassign logic...
    shipments_result = await db.execute(
        select(Shipment).where(Shipment.assigned_vehicle_id == vehicle_id)
    )
    assigned_shipments = shipments_result.scalars().all()
    
    for shipment in assigned_shipments:
        shipment.assigned_vehicle_id = None
        shipment.status = ShipmentStatus.PENDING
    
    await db.execute(delete(Vehicle).where(Vehicle.id == vehicle_id))
    await db.commit()
    
    # Return updated lists
    vehicles_result = await db.execute(select(Vehicle))
    vehicles = vehicles_result.scalars().all()
    shipments_result = await db.execute(select(Shipment))
    shipments = shipments_result.scalars().all()
    
    return {
        "message": f"Vehicle deleted successfully. {len(assigned_shipments)} shipments unassigned.",
        "vehicles": vehicles,
        "shipments": shipments
    }


# Shipment Endpoints

# SECURED: Creation requires Admin privileges
@app.post("/shipments", response_model=ShipmentResponse, dependencies=[Depends(verify_admin)])
async def create_shipment(shipment: ShipmentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new shipment (Admin Only)."""
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


@app.get("/shipments", response_model=list[ShipmentResponse], dependencies=[Depends(get_api_key)])
async def get_shipments(db: AsyncSession = Depends(get_db)):
    """Get all shipments (Authenticated)."""
    result = await db.execute(select(Shipment))
    shipments = result.scalars().all()
    return shipments


@app.get("/shipments/{shipment_id}", response_model=ShipmentResponse, dependencies=[Depends(get_api_key)])
async def get_shipment(shipment_id: str, db: AsyncSession = Depends(get_db)):
    """Get specific shipment (Authenticated)."""
    result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


# SECURED: Deletion requires Admin privileges
@app.delete("/shipments/{shipment_id}", response_model=dict, dependencies=[Depends(verify_admin)])
async def delete_shipment(shipment_id: str, db: AsyncSession = Depends(get_db)):
    """Delete shipment (Admin Only)."""
    result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    if shipment.assigned_vehicle_id:
        vehicle_result = await db.execute(
            select(Vehicle).where(Vehicle.id == shipment.assigned_vehicle_id)
        )
        vehicle = vehicle_result.scalar_one_or_none()
        if vehicle:
            vehicle.current_load = max(0.0, vehicle.current_load - shipment.weight)
    
    await db.execute(delete(Shipment).where(Shipment.id == shipment_id))
    await db.commit()
    
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
@app.post("/geocode", response_model=GeocodeResponse, dependencies=[Depends(get_api_key)])
async def geocode(request: GeocodeRequest):
    """Convert address to coordinates (Authenticated)."""
    try:
        result = await geocode_address(request.address)
        return result
    except ValueError as e:
        logger.warning(f"⚠️ Geocoding failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ API error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Geocoding failed: {str(e)}")


# Allocation Endpoint - Secured for Admin (Resource intensive)
@app.post("/allocate", response_model=AllocationResponse, dependencies=[Depends(verify_admin)])
async def allocate(db: AsyncSession = Depends(get_db)):
    """Auto-allocate shipments (Admin Only)."""
    logger.info("🔄 Allocation process started")
    try:
        result = await allocate_shipments(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Allocation failed: {str(e)}")


@app.post("/allocate/optimize", response_model=OptimizeAllocationResponse, dependencies=[Depends(verify_admin)])
async def optimize_allocate(db: AsyncSession = Depends(get_db)):
    """Optimize allocation (Admin Only)."""
    logger.info("🔄 Optimization process started")
    try:
        result = await optimize_allocation(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Optimization failed: {str(e)}")


@app.post("/allocations/manual", response_model=ManualAssignResponse, dependencies=[Depends(verify_admin)])
async def manual_assign_shipment(request: ManualAssignRequest, db: AsyncSession = Depends(get_db)):
    """Manual assignment (Admin Only)."""
    # ... (Keep existing manual assignment logic) ...
    shipment_result = await db.execute(select(Shipment).where(Shipment.id == request.shipment_id))
    shipment = shipment_result.scalar_one_or_none()
    if not shipment: raise HTTPException(status_code=404, detail="Shipment not found")

    vehicle_result = await db.execute(select(Vehicle).where(Vehicle.id == request.vehicle_id))
    vehicle = vehicle_result.scalar_one_or_none()
    if not vehicle: raise HTTPException(status_code=404, detail="Vehicle not found")

    if vehicle.current_load + shipment.weight > vehicle.max_capacity:
        raise HTTPException(status_code=400, detail="Capacity exceeded")

    # Range validation logic...
    dist_vehicle_pickup = calculate_distance(vehicle.latitude, vehicle.longitude, shipment.pickup_latitude, shipment.pickup_longitude)
    dist_pickup_drop = calculate_distance(shipment.pickup_latitude, shipment.pickup_longitude, shipment.drop_latitude, shipment.drop_longitude)
    if (dist_vehicle_pickup + dist_pickup_drop) > vehicle.max_range * 1.2:
        raise HTTPException(status_code=400, detail="Range exceeded")

    if shipment.assigned_vehicle_id:
        old_v = (await db.execute(select(Vehicle).where(Vehicle.id == shipment.assigned_vehicle_id))).scalar_one_or_none()
        if old_v: old_v.current_load = max(0.0, old_v.current_load - shipment.weight)

    shipment.assigned_vehicle_id = vehicle.id
    shipment.status = ShipmentStatus.ASSIGNED
    vehicle.current_load += shipment.weight
    
    await db.commit()
    await db.refresh(shipment)
    await db.refresh(vehicle)
    
    return ManualAssignResponse(
        message=f"Shipment assigned to {vehicle.name}",
        shipment=ShipmentResponse.model_validate(shipment),
        vehicle=VehicleResponse.model_validate(vehicle)
    )


@app.get("/vehicles/{vehicle_id}/route", response_model=RouteResponse, dependencies=[Depends(get_api_key)])
async def get_vehicle_route(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    """Get optimized route (Authenticated)."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    try:
        route = await calculate_route_with_precedence(db, vehicle_id)
        return route
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Route calculation failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
