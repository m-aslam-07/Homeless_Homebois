# ⚠️ CRITICAL: Database Reset Required

## 🚨 Why You Need to Reset

The Shipment model was changed from:
- ❌ Old: `address`, `latitude`, `longitude`
- ✅ New: `pickup_address`, `pickup_latitude`, `pickup_longitude`, `drop_address`, `drop_latitude`, `drop_longitude`

**The old database structure is incompatible with the new code!**

---

## ✅ Solution: Reset Database

### **Run This Command:**

```bash
docker-compose down -v
docker-compose up --build
```

**What this does:**
- `down -v` = Stops containers AND removes volumes (deletes database)
- `up --build` = Rebuilds and starts with fresh database

---

## 📋 Step-by-Step

### Step 1: Stop Everything
```bash
docker-compose down -v
```

### Step 2: Rebuild and Start
```bash
docker-compose up --build
```

### Step 3: Wait for Startup
Wait until you see:
```
logitech_backend   | ✅ Database tables initialized successfully
logitech_backend   | INFO:     Application startup complete.
```

### Step 4: Verify
- Open http://localhost:8000/health
- Should see: `{"status":"healthy"}`

---

## ⚠️ Important Notes

1. **This will DELETE all existing data** (vehicles, shipments)
2. **This is necessary** for the schema change
3. **After reset**, you'll need to recreate vehicles and shipments
4. **The new schema** supports pickup and drop locations

---

## ✅ After Reset

The database will have:
- ✅ New Shipment table with pickup/drop fields
- ✅ All constraints and validations
- ✅ Fresh start with compatible schema

**Then the network error should be fixed!**
