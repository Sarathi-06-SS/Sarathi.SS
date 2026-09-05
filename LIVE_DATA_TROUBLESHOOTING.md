# 🌱 Live Data Connection - Troubleshooting Guide

## ✅ What's Been Fixed

### 1. **Default Data Initialization**
- System now starts with sample data (25.5°C, 65% humidity, etc.)
- Data appears immediately without waiting for UDP signals

### 2. **Flexible UDP Data Parsing**
- Handles multiple data formats
- Automatically validates sensor values
- Default fallback values if parsing fails

### 3. **Test Data Generator**
- Automatically generates realistic test data if UDP inactive for 10+ seconds
- Simulates fluctuating sensor readings
- Helps test UI without hardware

### 4. **Enhanced Frontend Display**
- Connection status badge at the top of the page
- Shows "Connected" ✅, "Test Mode" ⚠️, or "Error" ❌
- Real-time feedback on data source
- Console logging for debugging

### 5. **Better Error Handling**
- Graceful fallback if data fetch fails
- No more broken metrics display
- Smooth animations continue with test data

---

## 🚀 How to Run

### **Option 1: Using Flask (Recommended)**
```bash
cd "f:\GUNAL 2025\HARDWARE PROJECT 2025-26\SOIL_CROP_ECOM\SENSOR DATA READ 3.10.0"
python main.py
```

Then open: **http://127.0.0.1:5000**

### **Option 2: Test Data Connection**
```bash
python debug_data.py
```

This will test if the `/data` endpoint is working correctly.

---

## 📊 Data Structure

The system displays 9 metrics:

| Metric | Unit | Example | Source |
|--------|------|---------|--------|
| Temperature | °C | 25.5 | UDP or Test |
| Humidity | % | 65.0 | UDP or Test |
| Soil Moisture | % | 70.0 | UDP or Test |
| Soil pH | (0-14) | 6.8 | UDP or Test |
| Nitrogen (N) | mg/kg | 45.2 | UDP or Test |
| Phosphorus (P) | mg/kg | 38.5 | UDP or Test |
| Potassium (K) | mg/kg | 52.1 | UDP or Test |
| Light Intensity | - | 450 | UDP or Test |
| Soil Status | - | High/Medium/Low | AI Prediction |

---

## 🔧 UDP Data Format

If you have sensors sending UDP data:

**Port:** 4210  
**Format:** `temp,humidity,light,moisture,pH,N,P,K`  
**Example:** `25.5,65,450,70,6.8,45.2,38.5,52.1`

---

## ⚠️ Troubleshooting

### **Problem: No data showing on page**

**Solution 1:** Check if Flask is running
```bash
python debug_data.py
```

**Solution 2:** Clear browser cache
- Press `Ctrl+Shift+Delete`
- Clear all cache for the site

**Solution 3:** Open browser console
- Press `F12` → Console tab
- Look for error messages
- Share the errors with support

---

### **Problem: "Test Mode" message appearing**

**This is normal!** It means:
- ✅ Flask server is running well
- ⚠️ No UDP sensor data is being received
- 📊 System is using simulated data for demonstration

**To use real sensor data:**
1. Start your sensor module
2. Ensure it sends UDP to `localhost:4210`
3. Data format: `temp,hum,light,moisture,pH,N,P,K`

---

### **Problem: Connection errors**

**Check:**
1. Flask server is running (`python main.py`)
2. No other app using port 5000
3. Firewall not blocking localhost connections

**Try:**
```bash
# Kill any process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Run Flask again
python main.py
```

---

## 📈 How Live Data Works

```
┌─────────────────┐
│ Sensor Hardware │ (UDP packets on port 4210)
└────────┬────────┘
         │
         ↓
┌─────────────────────────┐
│  UDP Listener Thread    │ (main.py)
│  - Parses sensor data   │
│  - Validates values     │
│  - Updates latest_data  │
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│  Test Data Generator    │ (Fallback)
│  - Activates if no UDP  │
│  - Generates random data│
│  - Keeps system running │
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│  Flask /data Endpoint   │ (Returns JSON)
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│  Frontend index.html    │ (Fetches every 5 sec)
│  - Updates metric cards │
│  - Updates charts       │
│  - Shows connection status
└─────────────────────────┘
```

---

## 🎯 Status Indicators

| Status | Icon | Meaning | Action |
|--------|------|---------|--------|
| Connected | ✅ | Real UDP data | None needed |
| Test Mode | ⚠️ | No UDP (simulated) | Check hardware |
| Error | ❌ | Connection failed | Restart Flask |

---

## 🛠️ Developer Notes

- **Frontend refresh rate:** 5 seconds
- **Test data update rate:** 5 seconds
- **UDP timeout:** 10 seconds (before test data activates)
- **Chart history:** Last 20 data points
- **Debug logging:** Check browser console (F12)

---

## 📱 Accessing from Other Devices

On Windows:
1. Find your computer's IP address: `ipconfig`
2. Replace `127.0.0.1` with your IP (e.g., `192.168.1.100`)
3. URL: `http://192.168.1.100:5000`

---

## 📞 Support

Check the console output for:
- `✅ UDP Sender Started` - Hardware connected
- `⚠️  No UDP data received` - Using test mode
- `❌ UDP Error` - Connection issue
- `📡 Received X UDP packets` - Data coming in

---

**Last Updated:** March 1, 2026  
**System Status:** 🟢 Fully Operational
