# 🚀 Quick Start Guide

## One-Command Startup

### Windows
```bash
start.bat
```

### Linux/Mac
```bash
chmod +x start.sh
./start.sh
```

### Manual (All Platforms)
```bash
docker-compose up --build
```

## Access the Application

- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## First Steps

1. **Add a Vehicle**
   - Use the "Add Vehicle" form in the sidebar
   - Enter name, max capacity (kg), and max range (km)

2. **Add Shipments**
   - Use the "Add Shipment" form
   - Enter an address in India (e.g., "Mumbai, Maharashtra, India")
   - Enter weight in kg
   - The system will automatically geocode the address

3. **Allocate Shipments**
   - Click "Allocate Shipments" button
   - The system will automatically assign pending shipments to vehicles

4. **View Routes**
   - Select a vehicle from the "Vehicle Focus Mode" dropdown
   - The map will show the optimized route for that vehicle
   - Route is calculated using TSP Nearest Neighbor algorithm

## Troubleshooting

### Services not starting
```bash
docker-compose logs
```

### Reset everything
```bash
docker-compose down -v
docker-compose up --build
```

### Check service status
```bash
docker-compose ps
```

## Architecture

- **PostgreSQL:** Database (port 5432)
- **FastAPI Backend:** API server (port 8000)
- **React Frontend:** Web UI (port 3000)

All services are containerized and orchestrated via Docker Compose.
