from pydantic import BaseModel, Field
from typing import Optional
from models import ShipmentStatus


# India Bounds Constants
INDIA_LAT_MIN = 6.0
INDIA_LAT_MAX = 38.0
INDIA_LON_MIN = 68.0
INDIA_LON_MAX = 98.0


class VehicleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    max_capacity: float = Field(..., gt=0)
    current_load: float = Field(default=0.0, ge=0)
    max_range: float = Field(..., gt=0)
    current_address: Optional[str] = Field(default=None)  # Optional address for geocoding
    latitude: Optional[float] = Field(default=None, ge=INDIA_LAT_MIN, le=INDIA_LAT_MAX)  # Optional if address provided
    longitude: Optional[float] = Field(default=None, ge=INDIA_LON_MIN, le=INDIA_LON_MAX)  # Optional if address provided


class VehicleResponse(BaseModel):
    id: str
    name: str
    max_capacity: float
    current_load: float
    max_range: float
    current_address: Optional[str]
    latitude: float
    longitude: float

    class Config:
        from_attributes = True


class ShipmentCreate(BaseModel):
    # Pickup location
    pickup_address: str = Field(..., min_length=1)
    pickup_latitude: float = Field(..., ge=INDIA_LAT_MIN, le=INDIA_LAT_MAX)
    pickup_longitude: float = Field(..., ge=INDIA_LON_MIN, le=INDIA_LON_MAX)
    
    # Drop location
    drop_address: str = Field(..., min_length=1)
    drop_latitude: float = Field(..., ge=INDIA_LAT_MIN, le=INDIA_LAT_MAX)
    drop_longitude: float = Field(..., ge=INDIA_LON_MIN, le=INDIA_LON_MAX)
    
    weight: float = Field(..., gt=0)
    status: ShipmentStatus = Field(default=ShipmentStatus.PENDING)
    assigned_vehicle_id: Optional[str] = None

    def validate_pickup_drop_different(self):
        """Validate that pickup and drop locations are different."""
        if (self.pickup_latitude == self.drop_latitude and 
            self.pickup_longitude == self.drop_longitude):
            raise ValueError("Pickup and drop locations cannot be the same")
        return self


class ShipmentResponse(BaseModel):
    id: str
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float
    drop_address: str
    drop_latitude: float
    drop_longitude: float
    weight: float
    status: ShipmentStatus
    assigned_vehicle_id: Optional[str] = None

    class Config:
        from_attributes = True


class GeocodeRequest(BaseModel):
    address: str = Field(..., min_length=1)


class GeocodeResponse(BaseModel):
    latitude: float
    longitude: float
    address: str


class AllocationResponse(BaseModel):
    assigned: int
    failed: int
    message: str


class OptimizeAllocationResponse(BaseModel):
    allocated: int
    unassigned: int
    vehicles_used: int
    message: str


class RouteResponse(BaseModel):
    vehicle_id: str
    route: list[list[float]]  # [[lat, lon], [lat, lon], ...]
    total_distance: float
