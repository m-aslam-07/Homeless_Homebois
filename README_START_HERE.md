# 🎯 START HERE - LogiTech Quick Start

## ⚡ Fastest Way to Run (3 Steps)

### Step 1: Open Terminal
- **Windows:** Press `Win + R`, type `cmd`, press Enter
- **Mac/Linux:** Open Terminal

### Step 2: Navigate to Project
```bash
cd "C:\Users\Mohamed Aslam\Documents - 2\Desktop\B2B Project"
```

### Step 3: Run This Command
```bash
docker-compose up --build
```

**That's it!** Wait 5-10 minutes for the first build, then open:

🌐 **http://localhost:3000** in your browser

---

## 🚀 Alternative: Use Startup Scripts

### Windows:
Double-click `START.bat` or run:
```bash
START.bat
```

### Mac/Linux:
```bash
chmod +x START.sh
./START.sh
```

---

## 📋 What Happens?

1. ✅ Downloads PostgreSQL database
2. ✅ Builds Python FastAPI backend
3. ✅ Builds React frontend
4. ✅ Starts all services
5. ✅ Creates database tables automatically

---

## 🌐 Access Points

Once running, open these URLs:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main application |
| **Backend API** | http://localhost:8000 | API server |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health** | http://localhost:8000/health | Health check |

---

## ✅ Verify It's Working

1. Open http://localhost:3000
2. You should see a map of India
3. Try adding a vehicle using the form
4. Try adding a shipment

---

## 🛑 Stop the Application

Press `Ctrl + C` in the terminal, or run:
```bash
docker-compose down
```

---

## 🐛 Having Issues?

### Check Docker is Running
```bash
docker ps
```

### View Logs
```bash
docker-compose logs -f
```

### Clean Start (Removes All Data)
```bash
docker-compose down -v
docker-compose up --build
```

### Common Issues:
- **Port in use?** Stop other services using ports 3000 or 8000
- **Build fails?** Check internet connection (needs to download images)
- **Can't connect?** Wait 1-2 minutes after build completes

---

## 📚 More Help

- **Detailed Setup:** See `SETUP_GUIDE.md`
- **All Commands:** See `RUN_COMMANDS.md`
- **Fixes Applied:** See `FIXES_APPLIED.md`

---

## 🎉 Success!

If you see the map at http://localhost:3000, **everything is working!**

**Next Steps:**
1. Add a vehicle (name, capacity, range)
2. Add a shipment (address in India, weight)
3. Click "Allocate Shipments"
4. Select a vehicle to see its route

---

**Need help? Check the logs:**
```bash
docker-compose logs -f
```
