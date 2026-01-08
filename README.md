# Route Planning & Resource Allocation System

A production-grade, containerized route planning and resource allocation web application built for a "Build to Break" Hackathon. The system provides an end-to-end workflow for managing vehicle fleets, creating shipments across India, automatically allocating work using Vehicle Routing Problem (VRP) heuristics, and visualizing routes on an interactive map.

## Quick Start

### Prerequisites
- Docker & Docker Compose installed and running

### One-Command Startup

```bash
docker-compose up --build
```

This will start:
- **PostgreSQL** database on port `5432`
- **FastAPI Backend** API server on port `8000`
- **React Frontend** web application on port `3000`

### Access the Application

- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** React, TypeScript, Vite, TailwindCSS, React-Leaflet
- **Deployment:** Docker & Docker Compose
- **Routing:** OSRM (Open Source Routing Machine) with fallback to Haversine distance
- **Geocoding:** Nominatim (OpenStreetMap) via geopy

## Key Features

- **Auto-Allocation Engine:** First Fit Decreasing algorithm for efficient vehicle-shipment assignment
- **Point-to-Point Shipments:** Separate pickup and drop locations with dual geocoding
- **Interactive Map Visualization:** Real road routing with automatic fallback
- **India-Only Operations:** Strict geographic bounds enforcement
- **Fault-Tolerant Design:** Comprehensive error handling and defensive coding

## Documentation Reference

For detailed technical logs, vulnerability fixes, architecture decisions, implementation notes, and troubleshooting guides, please see [APPENDIX.md](./APPENDIX.md).
# Homeless_Homebois
