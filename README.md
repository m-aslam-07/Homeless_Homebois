# LogiTech - Route Planning & Resource Allocation System

A production-grade, containerized route planning and resource allocation web application built for a "Build to Break" Hackathon. The system is designed to be fault-tolerant, defensive, and operates strictly within India.

## 🏗️ Architecture

- **Type:** Modular Monolith (Containerized)
- **Frontend:** React + TypeScript + Vite + TailwindCSS + React-Leaflet
- **Backend:** Python (FastAPI) + Pydantic (Validation)
- **Database:** PostgreSQL (Async via SQLAlchemy)
- **Routing Logic:** Python `haversine` library
- **Geocoding:** `geopy` (Nominatim) with defensive error handling
- **Deployment:** Docker & Docker Compose

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose installed
- Git

### One-Command Startup

```bash
docker-compose up --build
```

This will start:
- **PostgreSQL** on port `5432`
- **Backend API** on port `8000`
- **Frontend** on port `3000`

### Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 📋 Features

### Backend Features

1. **Defensive Geocoding**
   - User-Agent header to avoid 403 blocks
   - India bounds validation (Lat: 6-38, Lon: 68-98)
   - Comprehensive error handling (no 500 errors)

2. **Auto-Allocation Engine**
   - Greedy Bin Packing algorithm
   - Sorts shipments by weight (descending)
   - Assigns to first available vehicle with capacity

3. **Route Optimization**
   - TSP Nearest Neighbor algorithm
   - Uses haversine distance calculation
   - Returns optimized route coordinates

4. **Database Constraints**
   - SQL-level validation for India bounds
   - Capacity constraints (current_load <= max_capacity)
   - Non-negative weight validation

### Frontend Features

1. **Interactive Map (React-Leaflet)**
   - Locked to India bounds
   - Vehicle markers (truck icons)
   - Shipment markers (color-coded by status)
   - Route visualization with polylines

2. **Vehicle Focus Mode**
   - Select vehicle from dropdown
   - View only that vehicle's route
   - Auto-zoom to route bounds

3. **Input Forms**
   - Add Vehicle (name, capacity, range)
   - Add Shipment (address + weight with geocoding)
   - Auto-allocation button

## 🗄️ Database Schema

### Vehicle
- `id` (UUID)
- `name` (String)
- `max_capacity` (Float)
- `current_load` (Float, Default 0)
- `max_range` (Float)
- `latitude` (Float, Default: 20.59)
- `longitude` (Float, Default: 78.96)

**Constraints:**
- `current_load >= 0`
- `current_load <= max_capacity`

### Shipment
- `id` (UUID)
- `address` (String)
- `latitude` (Float)
- `longitude` (Float)
- `weight` (Float)
- `status` (Enum: PENDING, ASSIGNED, DELIVERED)
- `assigned_vehicle_id` (FK, nullable)

**Constraints:**
- `latitude` between 6.0 and 38.0 (India)
- `longitude` between 68.0 and 98.0 (India)
- `weight > 0`

## 🔌 API Endpoints

### Vehicles
- `GET /vehicles` - List all vehicles
- `GET /vehicles/{id}` - Get vehicle by ID
- `POST /vehicles` - Create vehicle

### Shipments
- `GET /shipments` - List all shipments
- `GET /shipments/{id}` - Get shipment by ID
- `POST /shipments` - Create shipment

### Operations
- `POST /geocode` - Geocode address to coordinates
- `POST /allocate` - Auto-allocate pending shipments
- `GET /vehicles/{id}/route` - Get optimized route for vehicle

## 🛡️ Security & Validation

1. **Input Validation**
   - Pydantic models for all inputs
   - SQL-level constraints for critical validations
   - India bounds enforced at multiple layers

2. **Error Handling**
   - All endpoints wrapped in try/except
   - Returns 400 (Bad Request) instead of 500 (Server Error)
   - User-friendly error messages

3. **Geocoding Protection**
   - Custom User-Agent to avoid rate limiting
   - Timeout handling
   - Connection error handling

## 🧪 Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## 📦 Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── services/
│   │   ├── geocoding.py     # Geocoding service
│   │   ├── allocation.py    # Allocation algorithm
│   │   └── routing.py       # Route optimization
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Backend container
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   └── App.tsx          # Main app component
│   ├── package.json         # Node dependencies
│   └── Dockerfile           # Frontend container
├── docker-compose.yml       # Orchestration
└── README.md                # This file
```

## 🎯 Hackathon Requirements Met

✅ **Fault-Tolerant:** Zero 500 errors, comprehensive error handling  
✅ **Defensive:** Strict input validation at multiple layers  
✅ **India-Only:** Geographic bounds enforced at DB and API level  
✅ **Containerized:** One-command startup with Docker Compose  
✅ **Production-Grade:** Proper error handling, validation, and structure  
✅ **Modular Monolith:** Clean separation of concerns  

## 📝 License

Built for Hackathon purposes.
