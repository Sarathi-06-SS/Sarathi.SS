"""
Test Script to Verify pH Value Reading is Working
This script simulates UDP sensor data and verifies the Flask endpoint
"""

import requests
import socket
import time
import json

# Test 1: Check if Flask server is running
print("\n" + "="*70)
print("🧪 pH VALUE READING - COMPREHENSIVE TEST")
print("="*70)

print("\n📋 TEST 1: Check Flask Server Status")
print("-" * 70)

try:
    response = requests.get("http://127.0.0.1:5000/data", timeout=3)
    if response.status_code == 200:
        data = response.json()
        print("✅ Flask server is running!")
        print(f"   pH value from server: {data.get('pH', 'N/A')}")
        print(f"   All sensor data: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Flask server returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Flask server!")
    print("   Make sure Flask is running: python main.py")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Send test UDP data
print("\n📋 TEST 2: Send Test UDP Data with pH")
print("-" * 70)

try:
    UDP_IP = "127.0.0.1"
    UDP_PORT = 4210
    
    # Format: temp,humidity,light,moisture,pH,N,P,K
    test_data = "25.5,65,450,70,6.8,45.2,38.5,52.1"
    
    print(f"📤 Sending UDP packet to {UDP_IP}:{UDP_PORT}")
    print(f"   Data: {test_data}")
    print(f"   Format: temp,humidity,light,moisture,pH,N,P,K")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(test_data.encode(), (UDP_IP, UDP_PORT))
    sock.close()
    
    print("✅ UDP packet sent!")
    
    # Wait a moment for the server to process
    time.sleep(2)
    
    # Test 3: Verify data was updated
    print("\n📋 TEST 3: Verify Data Was Updated by Server")
    print("-" * 70)
    
    response = requests.get("http://127.0.0.1:5000/data", timeout=3)
    if response.status_code == 200:
        data = response.json()
        print("✅ Data received from server:")
        print(f"   Temperature: {data.get('temp')}°C")
        print(f"   Humidity: {data.get('hum')}%")
        print(f"   Moisture: {data.get('moisture')}%")
        print(f"   Light: {data.get('light')}")
        print(f"   ✨ pH VALUE: {data.get('pH')} ✨")
        print(f"   Nitrogen (N): {data.get('N')}")
        print(f"   Phosphorus (P): {data.get('P')}")
        print(f"   Potassium (K): {data.get('K')}")
        print(f"   Prediction: {data.get('prediction')}")
        print(f"   Confidence: {data.get('confidence')}%")
        
        # Verify pH value is correct
        if data.get('pH') == 6.8:
            print("\n✅ pH VALUE READING SUCCESSFUL!")
        else:
            print(f"\n⚠️  pH value mismatch - expected 6.8, got {data.get('pH')}")
    
except socket.error as e:
    print(f"❌ Socket error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Test with different pH values
print("\n📋 TEST 4: Test Multiple pH Values")
print("-" * 70)

test_cases = [
    ("5.5,65,450,70,4.2,45,38,52", "Acidic soil"),
    ("25.5,65,450,70,7.0,45,38,52", "Neutral soil"),
    ("25.5,65,450,70,8.5,45,38,52", "Alkaline soil"),
]

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    for test_data, description in test_cases:
        print(f"\n  Testing: {description}")
        print(f"  Data: {test_data}")
        
        sock.sendto(test_data.encode(), (UDP_IP, UDP_PORT))
        time.sleep(1)
        
        response = requests.get("http://127.0.0.1:5000/data", timeout=3)
        if response.status_code == 200:
            data = response.json()
            expected_ph = float(test_data.split(",")[4])
            actual_ph = data.get('pH')
            
            if abs(actual_ph - expected_ph) < 0.01:
                print(f"  ✅ pH reading correct: {actual_ph}")
            else:
                print(f"  ⚠️  pH mismatch - expected {expected_ph}, got {actual_ph}")
    
    sock.close()
    
except Exception as e:
    print(f"❌ Error during test: {e}")

print("\n" + "="*70)
print("✅ Test Complete!")
print("="*70)
print("\n💡 Summary:")
print("  If all tests passed:")
print("  ✅ pH values are being read correctly")
print("  ✅ UDP data parsing is working")
print("  ✅ Flask endpoints are responding properly")
print("\n  Open browser at: http://127.0.0.1:5000")
print("  Check 'Soil pH Category' metric card for live pH values")
print("="*70 + "\n")
