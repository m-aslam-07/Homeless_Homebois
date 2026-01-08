# 🔧 Network Error Fix - Geocoding Issue

## Problem
Network error when entering source and destination addresses during geocoding.

## Root Causes Identified

1. **API URL Configuration**: Frontend may not be connecting to backend correctly
2. **Error Handling**: Network errors not being displayed clearly
3. **Timeout Issues**: No timeout set, causing hanging requests
4. **CORS/Connection**: Backend may not be accessible from frontend

## Fixes Applied

### 1. Enhanced Error Handling
- Added axios response interceptor
- Better error message extraction
- Clear network error messages
- 30-second timeout added

### 2. Improved Error Display
- Shows actual error messages from backend
- Distinguishes between network errors and API errors
- Better user feedback

### 3. API Configuration
- Added timeout to prevent hanging
- Better error messages for connection issues

## How to Verify Backend is Running

### Check Backend Health:
```bash
# In browser or terminal
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### Check Backend Logs:
```bash
docker-compose logs backend
```

### Check if Backend Container is Running:
```bash
docker ps | grep backend
```

## Common Issues & Solutions

### Issue 1: Backend Not Running
**Solution:**
```bash
docker-compose up backend
```

### Issue 2: Port Conflict
**Solution:**
- Check if port 8000 is in use
- Stop conflicting service
- Restart: `docker-compose restart backend`

### Issue 3: CORS Error
**Solution:**
- Backend CORS is configured
- Check backend logs for CORS errors
- Verify backend/main.py has CORS middleware

### Issue 4: Geocoding Service Down
**Solution:**
- Nominatim (geopy) may be rate-limited
- Wait a few seconds and try again
- Check backend logs for geocoding errors

## Testing the Fix

1. **Verify Backend:**
   - Open http://localhost:8000/health
   - Should see `{"status":"healthy"}`

2. **Test Geocoding:**
   - Open http://localhost:8000/docs
   - Try POST /geocode with address: "Mumbai, India"
   - Should return coordinates

3. **Test Frontend:**
   - Open http://localhost:3000
   - Try adding a shipment
   - Check browser console (F12) for errors

## Debug Steps

1. **Check Browser Console (F12)**
   - Look for network errors
   - Check if API calls are being made
   - Verify API URL

2. **Check Network Tab**
   - See if requests are reaching backend
   - Check response status codes
   - Verify request/response data

3. **Check Backend Logs**
   ```bash
   docker-compose logs -f backend
   ```
   - Look for geocoding errors
   - Check for connection issues

## Expected Behavior

### Successful Geocoding:
- Shows "Locating Pickup..." (green)
- Shows "Locating Drop..." (red)
- Both complete successfully
- Shipment created

### Network Error:
- Shows clear error message
- Indicates which address failed
- Suggests checking backend connection

## Additional Notes

- Geocoding uses Nominatim (OpenStreetMap)
- May be rate-limited (1 request per second)
- If rate-limited, wait and try again
- User-agent is set to avoid 403 errors
