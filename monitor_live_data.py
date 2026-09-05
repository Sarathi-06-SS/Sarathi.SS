"""
Real-Time Live Data Monitor
============================
Continuously monitors the /data endpoint and displays live updates.
Press Ctrl+C to stop.

This mimics what the frontend JavaScript does (polls every 2 seconds).
"""

import requests
import time
import os
from datetime import datetime

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_dashboard(data, cycle_count):
    """Display a nice dashboard of sensor data"""
    clear_screen()
    
    is_live = data.get('is_live', False)
    status_icon = "🟢" if is_live else "🔴"
    status_text = "LIVE" if is_live else "OFFLINE"
    
    print("╔" + "═"*68 + "╗")
    print("║" + " "*20 + "🌱 LIVE SENSOR MONITOR" + " "*25 + "║")
    print("╚" + "═"*68 + "╝")
    
    print(f"\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔄 Updates: {cycle_count}")
    print(f"📡 Status: {status_icon} {status_text}")
    
    print("\n" + "─"*70)
    print("📊 SENSOR READINGS")
    print("─"*70)
    
    # Environmental sensors
    print(f"\n🌡️  Temperature:  {data.get('temp', '--')} °C")
    print(f"💧  Humidity:     {data.get('hum', '--')} %")
    print(f"🌱  Moisture:     {data.get('moisture', '--')} %")
    print(f"☀️  Light:        {data.get('light', '--')} Lux")
    
    # Soil chemistry
    print(f"\n🧪  Soil pH:      {data.get('pH', '--')}")
    print(f"🔬  Nitrogen (N): {data.get('N', '--')} mg/kg")
    print(f"🔬  Phosphorus (P): {data.get('P', '--')} mg/kg")
    print(f"🔬  Potassium (K): {data.get('K', '--')} mg/kg")
    
    # AI Prediction
    print("\n" + "─"*70)
    print("🤖 AI SOIL HEALTH PREDICTION")
    print("─"*70)
    
    prediction = data.get('prediction', 'Unknown')
    confidence = data.get('confidence', 0)
    
    if prediction == 'High':
        pred_icon = "🟢"
    elif prediction == 'Medium':
        pred_icon = "🟡"
    elif prediction == 'Low':
        pred_icon = "🔴"
    else:
        pred_icon = "⚪"
    
    print(f"\n{pred_icon} Soil Condition: {prediction}")
    print(f"📊 Confidence:    {confidence}%")
    
    # Status bar
    confidence_bar_length = int(confidence / 2)  # Scale to 50 chars max
    bar = "█" * confidence_bar_length
    print(f"\n[{bar:<50}] {confidence}%")
    
    print("\n" + "─"*70)
    if is_live:
        print("✅ System receiving live UDP data from ESP32")
    else:
        print("⚠️  Waiting for UDP packets... Check ESP32 connection")
    print("─"*70)
    print("\n💡 Press Ctrl+C to stop monitoring")

def monitor_live(url="http://127.0.0.1:5000/data", interval=2):
    """Continuously monitor the data endpoint"""
    cycle = 0
    
    print("\n🚀 Starting live monitor...")
    print(f"📍 Endpoint: {url}")
    print(f"⏱️  Refresh: Every {interval} seconds\n")
    time.sleep(1)
    
    try:
        while True:
            try:
                response = requests.get(url, timeout=3)
                
                if response.status_code == 200:
                    data = response.json()
                    cycle += 1
                    display_dashboard(data, cycle)
                else:
                    clear_screen()
                    print(f"❌ HTTP Error {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                clear_screen()
                print("❌ Cannot connect to Flask server")
                print("   Make sure the server is running:")
                print("   python main.py")
                print("\n🔄 Retrying in 5 seconds...")
                time.sleep(5)
                continue
                
            except Exception as e:
                clear_screen()
                print(f"❌ Error: {e}")
                print("\n🔄 Retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            # Wait before next poll
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitor stopped by user")
        print("👋 Goodbye!\n")

if __name__ == "__main__":
    try:
        monitor_live()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
