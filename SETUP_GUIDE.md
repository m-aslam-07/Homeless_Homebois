# 🚀 LogiTech - Complete Setup & Run Guide

## Prerequisites

Before starting, ensure you have:
- **Docker Desktop** installed and running
- **Docker Compose** (comes with Docker Desktop)
- **Git** (optional, for cloning)

---

## 📋 Step-by-Step Setup Instructions

### Step 1: Verify Docker is Running

**Windows:**
```powershell
docker --version
docker-compose --version
```

**Linux/Mac:**
```bash
docker --version
docker-compose --version
```

If you see version numbers, Docker is installed. Make sure Docker Desktop is **running** (you should see the Docker icon in your system tray).

---

### Step 2: Navigate to Project Directory

Open your terminal/command prompt and navigate to the project folder:

```bash
cd "C:\Users\Mohamed Aslam\Documents - 2\Desktop\B2B Project"
```

Or if you're in a different location:
```bash
cd path/to/your/project
```

---

### Step 3: Clean Previous Builds (Optional but Recommended)

If you've run this before and want a fresh start:

```bash
docker-compose down -v
```

This removes all containers and volumes (including database data).

---

### Step 4: Build and Start All Services

**One-Command Startup:**

```bash
docker-compose up --build
```

This will:
1. Build the PostgreSQL database container
2. Build the FastAPI backend container
3. Build the React frontend container
4. Start all services in the correct order

**First time build may take 5-10 minutes** (downloading images and installing dependencies).

---

### Step 5: Wait for Services to Start

You'll see logs in your terminal. Wait until you see:

```
logitech_backend    | INFO:     Application startup complete.
logitech_frontend   | /docker-entrypoint.sh: Configuration complete; ready for start up
```

**This usually takes 30-60 seconds after the build completes.**

---

### Step 6: Access the Application

Once all services are running, open your web browser and go to:

- **🌐 Frontend (Main Application):** http://localhost:3000
- **🔧 Backend API:** http://localhost:8000
- **📚 API Documentation:** http://localhost:8000/docs
- **❤️ Health Check:** http://localhost:8000/health

---

## 🎯 Quick Start Commands

### Start Services (Background Mode)
```bash
docker-compose up -d --build
```

### View Logs
```bash
docker-compose logs -f
```

### View Specific Service Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Stop Services
```bash
docker-compose down
```

### Stop and Remove All Data
```bash
docker-compose down -v
```

### Restart a Specific Service
```bash
docker-compose restart backend
docker-compose restart frontend
```

---

## 🐛 Troubleshooting

### Issue 1: Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Find what's using the port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Mac/Linux

# Stop the conflicting service or change port in docker-compose.yml
```

### Issue 2: Docker Build Fails

**Error:** `npm install` fails or times out

**Solution:**
```bash
# Clean Docker cache and rebuild
docker-compose down
docker system prune -a
docker-compose up --build
```

### Issue 3: Frontend Can't Connect to Backend

**Error:** Network errors in browser console

**Solution:**
1. Check if backend is running: http://localhost:8000/health
2. Check CORS settings in `backend/main.py`
3. Verify environment variable: `VITE_API_URL=http://localhost:8000`

### Issue 4: Database Connection Errors

**Error:** `Connection refused` or `database does not exist`

**Solution:**
```bash
# Restart services in order
docker-compose down
docker-compose up postgres
# Wait 10 seconds, then:
docker-compose up backend frontend
```

### Issue 5: Frontend Shows Blank Page

**Solution:**
1. Check browser console for errors (F12)
2. Verify frontend container is running: `docker ps`
3. Check frontend logs: `docker-compose logs frontend`
4. Clear browser cache and hard refresh (Ctrl+Shift+R)

---

## ✅ Verification Checklist

After starting, verify everything works:

- [ ] **PostgreSQL** is running: `docker ps | grep postgres`
- [ ] **Backend** responds: http://localhost:8000/health returns `{"status": "healthy"}`
- [ ] **Frontend** loads: http://localhost:3000 shows the map
- [ ] **API Docs** accessible: http://localhost:8000/docs
- [ ] Can create a vehicle via the form
- [ ] Can create a shipment via the form
- [ ] Auto-Allocate button works
- [ ] Map displays markers correctly

---

## 🧪 Test the Application

### 1. Add a Vehicle
- Use the "Add Vehicle" form in the sidebar
- Enter: Name="Truck-1", Max Capacity=1000, Max Range=500
- Click "Add Vehicle"

### 2. Add a Shipment
- Use the "Add Shipment" form
- Enter: Address="Mumbai, Maharashtra, India", Weight=200
- Click "Add Shipment" (it will geocode the address)

### 3. Auto-Allocate
- Click "Allocate Shipments" button
- Check the result message

### 4. View Route
- Select a vehicle from "Vehicle Focus Mode" dropdown
- The map will show the optimized route

---

## 📊 Service Status Commands

### Check Running Containers
```bash
docker ps
```

### Check All Containers (Including Stopped)
```bash
docker ps -a
```

### Check Service Health
```bash
docker-compose ps
```

### View Resource Usage
```bash
docker stats
```

---

## 🔄 Development Mode

If you want to develop and see changes in real-time:

### Backend (Hot Reload)
The backend already has hot reload enabled via `--reload` flag in docker-compose.yml.

### Frontend (Hot Reload)
For frontend development, run locally instead of Docker:

```bash
cd frontend
npm install
npm run dev
```

Then access: http://localhost:5173

---

## 🗑️ Cleanup Commands

### Remove All Containers and Volumes
```bash
docker-compose down -v
```

### Remove All Images
```bash
docker-compose down --rmi all
```

### Complete Cleanup (Nuclear Option)
```bash
docker-compose down -v --rmi all
docker system prune -a
```

---

## 📝 Environment Variables

### Backend
- `DATABASE_URL` - PostgreSQL connection string (set in docker-compose.yml)

### Frontend
- `VITE_API_URL` - Backend API URL (set in docker-compose.yml)

To modify, edit `docker-compose.yml` and rebuild.

---

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ All three containers are running (`docker ps` shows 3 containers)
2. ✅ http://localhost:3000 shows the map interface
3. ✅ http://localhost:8000/docs shows the API documentation
4. ✅ You can create vehicles and shipments without errors
5. ✅ The map displays markers and routes correctly

---

## 📞 Need Help?

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify Docker is running: `docker ps`
3. Check port availability
4. Review the troubleshooting section above
5. Ensure all prerequisites are installed

---

## 🚀 Quick Reference

| Action | Command |
|--------|---------|
| Start | `docker-compose up --build` |
| Start (Background) | `docker-compose up -d --build` |
| Stop | `docker-compose down` |
| View Logs | `docker-compose logs -f` |
| Restart | `docker-compose restart` |
| Clean Start | `docker-compose down -v && docker-compose up --build` |

---

**🎊 You're all set! The application should now be running perfectly!**
