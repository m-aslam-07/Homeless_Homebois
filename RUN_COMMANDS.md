# ⚡ Quick Run Commands - LogiTech

## 🚀 Start the Application

### Option 1: One-Command Start (Recommended)
```bash
docker-compose up --build
```

### Option 2: Start in Background
```bash
docker-compose up -d --build
```

### Option 3: Clean Start (Removes Old Data)
```bash
docker-compose down -v && docker-compose up --build
```

---

## 🛑 Stop the Application

```bash
docker-compose down
```

### Stop and Remove All Data
```bash
docker-compose down -v
```

---

## 📊 View Status

### Check Running Containers
```bash
docker ps
```

### View Logs (All Services)
```bash
docker-compose logs -f
```

### View Specific Service Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

---

## 🔄 Restart Services

### Restart All
```bash
docker-compose restart
```

### Restart Specific Service
```bash
docker-compose restart backend
docker-compose restart frontend
```

---

## 🧹 Cleanup Commands

### Remove Containers and Volumes
```bash
docker-compose down -v
```

### Remove Everything (Including Images)
```bash
docker-compose down -v --rmi all
```

### Complete System Cleanup
```bash
docker-compose down -v --rmi all
docker system prune -a
```

---

## 🌐 Access URLs

After starting, access:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## ✅ Verify Everything Works

```bash
# Check containers are running
docker ps

# Check backend health
curl http://localhost:8000/health

# View all logs
docker-compose logs
```

---

## 🐛 Common Issues & Fixes

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Mac/Linux
lsof -i :8000
lsof -i :3000
```

### Rebuild After Code Changes
```bash
docker-compose up --build
```

### Database Issues
```bash
docker-compose down -v
docker-compose up --build
```

---

**💡 Tip:** Keep the terminal open to see logs. Press `Ctrl+C` to stop when running in foreground mode.
