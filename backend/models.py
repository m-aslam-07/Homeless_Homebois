from sqlalchemy import Column, String, Float, ForeignKey, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from database import Base


class ShipmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    DELIVERED = "DELIVERED"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    max_capacity = Column(Float, nullable=False)
    current_load = Column(Float, default=0.0, nullable=False)
    max_range = Column(Float, nullable=False)
    current_address = Column(String, nullable=True)  # Optional: can be set via geocoding
    latitude = Column(Float, default=20.59)  # Default to India center
    longitude = Column(Float, default=78.96)

    # Relationship to shipments (for graceful deletion handling)
    shipments = relationship(
        "Shipment",
        back_populates="vehicle",
        cascade="save-update, merge, refresh-expire"
    )

    __table_args__ = (
        CheckConstraint('current_load >= 0', name='check_current_load_non_negative'),
        CheckConstraint('current_load <= max_capacity', name='check_current_load_within_capacity'),
        # Vehicle location India bounds
        CheckConstraint('latitude >= 6.0 AND latitude <= 38.0', name='check_vehicle_latitude_india'),
        CheckConstraint('longitude >= 68.0 AND longitude <= 98.0', name='check_vehicle_longitude_india'),
    )


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Pickup location (Source)
    pickup_address = Column(String, nullable=False)
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)
    
    # Drop location (Destination)
    drop_address = Column(String, nullable=False)
    drop_latitude = Column(Float, nullable=False)
    drop_longitude = Column(Float, nullable=False)
    
    weight = Column(Float, nullable=False)
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.PENDING, nullable=False)
    assigned_vehicle_id = Column(
        UUID(as_uuid=False),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationship to vehicle (for graceful deletion handling)
    vehicle = relationship("Vehicle", back_populates="shipments")

    __table_args__ = (
        # Pickup location India bounds
        CheckConstraint('pickup_latitude >= 6.0 AND pickup_latitude <= 38.0', name='check_pickup_latitude_india'),
        CheckConstraint('pickup_longitude >= 68.0 AND pickup_longitude <= 98.0', name='check_pickup_longitude_india'),
        # Drop location India bounds
        CheckConstraint('drop_latitude >= 6.0 AND drop_latitude <= 38.0', name='check_drop_latitude_india'),
        CheckConstraint('drop_longitude >= 68.0 AND drop_longitude <= 98.0', name='check_drop_longitude_india'),
        # Weight validation
        CheckConstraint('weight > 0', name='check_weight_positive'),
        # Prevent zero-distance shipments (pickup != drop)
        CheckConstraint(
            'NOT (pickup_latitude = drop_latitude AND pickup_longitude = drop_longitude)',
            name='check_pickup_drop_different'
        ),
    )
