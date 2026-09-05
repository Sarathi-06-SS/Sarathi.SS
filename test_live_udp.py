"""
Live UDP Test Script
====================
This script tests the complete UDP → Backend → Frontend data flow.

It will:
1. Send test UDP packets to port 4210
2. Query the /data endpoint to verify updates
3. Confirm live data is flowing correctly

Run this AFTER starting main.py server.
"""

import socket
import time
import requests
import json
from datetime import datetime

def send_test_udp_packet(port=4210):
    """Send a test UDP packet with sensor data"""
    try:
        # Simulate realistic sensor data
        test_packet = "TEMP:28.5,HUM:72.0,LDR:550,MOISTURE:68,PH:6.5,N:48.0,P:38.0,K:52.0"
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(test_packet.encode('utf-8'), ('127.0.0.1', port))
        sock.close()
        
        print(f"✅ Sent UDP packet: {test_packet}")
        return True
    except Exception as e:
        print(f"❌ Failed to send UDP: {e}")
        return False

def check_data_endpoint(url="http://127.0.0.1:5000/data"):
    """Query the /data endpoint and display results"""
    try:
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📊 Backend Response:")
            print(f"   └─ Live Status: {'🟢 LIVE' if data.get('is_live') else '🔴 OFFLINE'}")
            print(f"   └─ Temperature: {data.get('temp')}°C")
            print(f"   └─ Humidity: {data.get('hum')}%")
            print(f"   └─ Moisture: {data.get('moisture')}%")
            print(f"   └─ pH: {data.get('pH')}")
            print(f"   └─ N: {data.get('N')} mg/kg")
            print(f"   └─ P: {data.get('P')} mg/kg")
            print(f"   └─ K: {data.get('K')} mg/kg")
            print(f"   └─ Light: {data.get('light')} Lux")
            print(f"   └─ Prediction: {data.get('prediction')}")
            print(f"   └─ Confidence: {data.get('confidence')}%")
            
            return data
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {url}")
        print(f"   Make sure Flask server is running: python main.py")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_live_test(cycles=5):
    """Run a complete live data flow test"""
    print("\n" + "="*70)
    print("🔬 LIVE UDP DATA FLOW TEST")
    print("="*70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 UDP Target: 127.0.0.1:4210")
    print(f"🌐 Backend API: http://127.0.0.1:5000/data")
    print(f"🔄 Test Cycles: {cycles}")
    print("="*70 + "\n")
    
    # First check if backend is reachable
    print("Step 1: Checking backend availability...")
    initial_data = check_data_endpoint()
    
    if initial_data is None:
        print("\n⚠️  Backend is not running. Please start it first:")
        print("   python main.py")
        return False
    
    print(f"\n✅ Backend is online! Initial is_live status: {initial_data.get('is_live')}")
    
    # Now send test packets and verify updates
    print(f"\nStep 2: Sending {cycles} test UDP packets...")
    print("-" * 70)
    
    for i in range(1, cycles + 1):
        print(f"\n🔄 Cycle {i}/{cycles}:")
        print(f"   ⏱️  {datetime.now().strftime('%H:%M:%S')}")
        
        # Send UDP packet
        if send_test_udp_packet():
            # Wait a moment for processing
            time.sleep(0.5)
            
            # Check if data updated
            current_data = check_data_endpoint()
            
            if current_data and current_data.get('is_live'):
                print(f"   ✅ Data is LIVE and updating!")
            else:
                print(f"   ⚠️  Data not live yet. May need more time or check UDP port.")
        
        # Wait before next cycle
        if i < cycles:
            time.sleep(2)
    
    print("\n" + "="*70)
    print("✅ Test Complete!")
    print("\n💡 Summary:")
    print("   • If 'is_live' = true → UDP is working perfectly")
    print("   • If 'is_live' = false → Check:")
    print("     - Is ESP32 sending to port 4210?")
    print("     - Is firewall blocking UDP?")
    print("     - Check main.py terminal for UDP receive logs")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        run_live_test(cycles=5)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
