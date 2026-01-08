# 🔧 Troubleshooting Network Error - Geocoding

## Quick Diagnosis

### Step 1: Check if Backend is Running

Open your browser and go to:
```
http://localhost:8000/health
```

**Expected:** `{"status":"healthy"}`

**If you get an error:**
- Backend is not running
- Solution: `docker-compose up backend`

---

### Step 2: Check Backend Logs

```bash
docker-compose logs backend
```

Look for:
- ✅ "Application startup complete" = Backend is running
- ❌ Connection errors = Backend issue
- ❌ Geocoding errors = Nominatim service issue

---

### Step 3: Check Browser Console

1. Open browser (F12)
2. Go to **Console** tab
3. Try adding a shipment
4. Look for error messages

**Common errors:**
- `Network Error` = Backend not accessible
- `CORS error` = Backend CORS misconfigured
- `Timeout` = Backend too slow or geocoding timeout

---

### Step 4: Check Network Tab

1. Open browser (F12)
2. Go to **Network** tab
3. Try adding a shipment
4. Look for `/geocode` request

**Check:**
- Status code (should be 200)
- Request URL (should be http://localhost:8000/geocode)
- Response (should have coordinates)

---

## Common Issues & Solutions

### Issue 1: Backend Not Running

**Symptoms:**
- Network error immediately
- Cannot connect message

**Solution:**
```bash
# Check if backend container is running
docker ps | grep backend

# If not running, start it
docker-compose up backend

# Or restart everything
docker-compose restart
```

---

### Issue 2: Port 8000 Already in Use

**Symptoms:**
- Backend won't start
- Port conflict error

**Solution:**
```bash
# Find what's using port 8000
# Windows:
netstat -ano | findstr :8000

# Mac/Linux:
lsof -i :8000

# Stop the conflicting service or change port in docker-compose.yml
```

---

### Issue 3: Geocoding Service Rate Limited

**Symptoms:**
- Network error after a few seconds
- Backend logs show geocoding errors

**Solution:**
- Wait 1-2 seconds between requests
- Nominatim allows 1 request per second
- Try again after waiting

---

### Issue 4: CORS Error

**Symptoms:**
- Browser console shows CORS error
- Request blocked by browser

**Solution:**
- Backend CORS is already configured
- Check backend logs for CORS errors
- Verify backend/main.py has CORS middleware

---

### Issue 5: Frontend Can't Reach Backend

**Symptoms:**
- Network error
- Backend health check works but frontend can't connect

**Solution:**
1. Check API URL in browser console
2. Verify it's `http://localhost:8000`
3. Try accessing http://localhost:8000/docs directly
4. Check if backend is accessible from host machine

---

## Quick Fixes

### Fix 1: Restart Everything
```bash
docker-compose down
docker-compose up --build
```

### Fix 2: Check Backend Health
```bash
curl http://localhost:8000/health
```

### Fix 3: Test Geocoding Directly
```bash
curl -X POST http://localhost:8000/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "Mumbai, India"}'
```

### Fix 4: View Real-time Logs
```bash
docker-compose logs -f backend
```

---

## Expected Behavior

### ✅ Working:
1. Enter pickup address
2. See "Locating Pickup..." (green)
3. Geocoding completes
4. Enter drop address
5. See "Locating Drop..." (red)
6. Geocoding completes
7. Shipment created successfully

### ❌ Network Error:
1. Enter address
2. See loading indicator
3. Error message appears
4. Check backend logs for details

---

## Debug Information

### Check API URL:
Open browser console and type:
```javascript
console.log(import.meta.env.VITE_API_URL || 'http://localhost:8000')
```

### Test Backend Connection:
```javascript
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```

---

## Still Having Issues?

1. **Check all containers are running:**
   ```bash
   docker ps
   ```
   Should show: postgres, backend, frontend

2. **Check backend logs:**
   ```bash
   docker-compose logs backend | tail -50
   ```

3. **Check frontend logs:**
   ```bash
   docker-compose logs frontend | tail -50
   ```

4. **Restart specific service:**
   ```bash
   docker-compose restart backend
   ```

---

## Error Messages Explained

| Error | Meaning | Solution |
|-------|---------|----------|
| `Network Error` | Can't connect to backend | Check backend is running |
| `Request timeout` | Backend too slow | Check backend logs, wait and retry |
| `CORS error` | Browser blocking request | Check backend CORS config |
| `Geocoding service error` | Nominatim unavailable | Wait and try again |
| `Cannot geocode address` | Address not found | Try different address format |

---

**Most common fix: Restart the backend container!**

```bash
docker-compose restart backend
```
