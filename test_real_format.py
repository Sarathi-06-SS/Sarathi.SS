"""
Test Script for Actual Sensor Data Format
Tests pH reading with the actual format: temp,hum,light,moisture,unknown,pH_category_string,N,P,K
"""

import requests
import socket
import time
import json

print("\n" + "="*80)
print("🧪 SENSOR DATA FORMAT TEST - Real Sensor Format")
print("="*80)

# Test 1: Check Flask server
print("\n📋 TEST 1: Flask Server Status")
print("-" * 80)

try:
    response = requests.get("http://127.0.0.1:5000/data", timeout=3)
    if response.status_code == 200:
        data = response.json()
        print("✅ Flask server is running!")
        print(f"   Current pH: {data.get('pH', 'N/A')}")
    else:
        print(f"❌ Flask returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Flask server!")
    print("   Start it with: python main.py")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Send real sensor format data
print("\n📋 TEST 2: Send Actual Sensor Data (Real Format)")
print("-" * 80)

try:
    UDP_IP = "127.0.0.1"
    UDP_PORT = 4210
    
    # ACTUAL FORMAT from sensor: temp,hum,light,moisture,unknown_value,pH_category(string),N,P,K
    test_cases = [
        ("31.90,43.00,76,0,2261,ACID,0.00,0.00,0.00", "Acidic soil"),
        ("25.50,65.00,450,70,2500,NEUTRAL,45.20,38.50,52.10", "Neutral soil"),
        ("28.00,55.00,380,60,2400,BASE,40.00,35.00,48.00", "Alkaline soil"),
    ]
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    for test_data, description in test_cases:
        print(f"\n  📤 Testing: {description}")
        print(f"     Format: temp,hum,light,moisture,unknown,pH_category,N,P,K")
        print(f"     Data: {test_data}")
        
        sock.sendto(test_data.encode(), (UDP_IP, UDP_PORT))
        time.sleep(1.5)
        
        # Fetch and verify
        try:
            response = requests.get("http://127.0.0.1:5000/data", timeout=3)
            if response.status_code == 200:
                data = response.json()
                
                # Extract expected pH category from test data
                parts = test_data.split(",")
                expected_category = parts[5] if len(parts) > 5 else "UNKNOWN"
                
                print(f"     ✅ Received: pH={data.get('pH', 'N/A')} ({expected_category})")
                print(f"        Temp: {data.get('temp')}°C")
                print(f"        Humidity: {data.get('hum')}%")
                print(f"        Moisture: {data.get('moisture')}%")
                print(f"        N={data.get('N')}, P={data.get('P')}, K={data.get('K')}")
                
                # Verify pH mapping
                if expected_category == "ACID" and data.get('pH') == 6.0:
                    print(f"        ✅ pH mapping correct! ACID → 6.0")
                elif expected_category == "NEUTRAL" and data.get('pH') == 7.0:
                    print(f"        ✅ pH mapping correct! NEUTRAL → 7.0")
                elif expected_category == "BASE" and data.get('pH') == 8.0:
                    print(f"        ✅ pH mapping correct! BASE → 8.0")
        except Exception as e:
            print(f"     ❌ Error fetching response: {e}")
    
    sock.close()

except socket.error as e:
    print(f"❌ Socket error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Verify frontend displays properly
print("\n📋 TEST 3: Frontend Display Verification")
print("-" * 80)

print("  Open http://127.0.0.1:5000 in your browser")
print("  Check that:")
print("    ✅ Soil pH Category card shows the correct pH value")
print("    ✅ Color changes based on pH (Red=Acid, Green=Neutral, Blue=Base)")
print("    ✅ pH display updates in real-time from sensor data")

print("\n" + "="*80)
print("✅ Test Complete!")
print("="*80)
print("\n📊 Data Format Summary:")
print("  Real Sensor Format: temp,hum,light,moisture,unknown_value,pH_category_string,N,P,K")
print("  Example: 31.90,43.00,76,0,2261,ACID,0.00,0.00,0.00")
print("\n  pH Categories Accepted:")
print("    • ACID → Converted to pH value 6.0 (red color)")
print("    • NEUTRAL → Converted to pH value 7.0 (green color)")
print("    • BASE → Converted to pH value 8.0 (blue color)")
print("\n  Parser automatically strips whitespace and converts case")
print("="*80 + "\n")
