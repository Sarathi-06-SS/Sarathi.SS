"""
Debug Script to Test Live Data Connection
This script helps verify that the Flask /data endpoint is working correctly
"""

import requests
import json
import time
from datetime import datetime

def test_data_connection():
    """Test the /data endpoint"""
    print("\n" + "="*70)
    print("🔍 LIVE DATA CONNECTION TEST")
    print("="*70)
    
    url = "http://127.0.0.1:5000/data"
    
    print(f"\n📍 Testing endpoint: {url}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for i in range(1, 6):
        try:
            print(f"📡 Request #{i}...", end=" ")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ SUCCESS")
                print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                print(f"   Status Code: {response.status_code}")
                print(f"\n   📊 Data Received:")
                print(f"   ├─ Temperature: {data.get('temp', 'N/A')}°C")
                print(f"   ├─ Humidity: {data.get('hum', 'N/A')}%")
                print(f"   ├─ Moisture: {data.get('moisture', 'N/A')}%")
                print(f"   ├─ Soil pH: {data.get('pH', 'N/A')}")
                print(f"   ├─ Nitrogen (N): {data.get('N', 'N/A')}")
                print(f"   ├─ Phosphorus (P): {data.get('P', 'N/A')}")
                print(f"   ├─ Potassium (K): {data.get('K', 'N/A')}")
                print(f"   ├─ Light: {data.get('light', 'N/A')}")
                print(f"   ├─ Prediction: {data.get('prediction', 'N/A')}")
                print(f"   └─ Confidence: {data.get('confidence', 'N/A')}%\n")
                
            else:
                print(f"❌ FAILED - Status Code: {response.status_code}")
                print(f"   Response: {response.text}\n")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ CONNECTION ERROR")
            print(f"   ⚠️  Cannot connect to Flask server at {url}")
            print(f"   Make sure Flask server is running on port 5000\n")
            break
        except requests.exceptions.Timeout:
            print(f"❌ TIMEOUT")
            print(f"   Server took too long to respond\n")
        except Exception as e:
            print(f"❌ ERROR - {str(e)}\n")
        
        if i < 5:
            time.sleep(2)
    
    print("="*70)
    print("✅ Test Complete!")
    print("\n💡 Tips:")
    print("  • If all requests succeeded: Live data is working correctly")
    print("  • If CONNECTION ERROR: Start Flask server with: python main.py")
    print("  • Check browser at: http://127.0.0.1:5000")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        test_data_connection()
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
