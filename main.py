import sys
import io

# Fix stdout/stderr: line_buffering=True so UDP thread prints flush immediately
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import numpy as np
import joblib
import socket
import threading
import time
import os
import json
from tf_keras.models import load_model
from PIL import Image, ImageOps

# =====================================================
# FIX: SSL Certificate Verification
# =====================================================
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# =====================================================
# NEW Gemini SDK (google-genai)
# =====================================================
from google import genai

# =====================================================
# FLASK SETUP
# =====================================================
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =====================================================
# GEMINI SETUP
# BUG FIX #1: API key was malformed (started with "AQ." — not a valid Google AI key format).
#             Replace the placeholder below with your real key from https://aistudio.google.com
# BUG FIX #2: Model name "gemini-3.5-flash-lite" does not exist.
#             Correct name is "gemini-1.5-flash-latest" (or "gemini-1.5-flash").
# =====================================================
GEMINI_API_KEY = "YOUR_REAL_GEMINI_API_KEY_HERE"   # <-- paste your key here
GEMINI_MODEL  = "gemini-1.5-flash-latest"

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# =====================================================
# LOAD MODELS
# =====================================================
soil_model = joblib.load("quantum_xgboost_model.pkl")
soil_scaler = joblib.load("scaler.pkl")
soil_label_encoder = joblib.load("label_encoder.pkl")

fruit_model = load_model("keras_model.h5", compile=False)

CLASS_NAMES = [
    "Apple___Apple_scab",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Corn_(maize)___Cercospora_leaf_spot_Gray_leaf_spot",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___healthy",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Strawberry___healthy",
    "Strawberry___Leaf_scorch"
]

# =====================================================
# THREAD SAFE STORAGE
# =====================================================
data_lock = threading.Lock()
udp_data_count = 0  # Counter to track received UDP packets
last_udp_time = 0.0  # Track last UDP packet time

# Initialize with default data
latest_data = {
    "temp": 0.0,
    "hum": 0.0,
    "light": 0,
    "moisture": 0,
    "N": 0.0,
    "P": 0.0,
    "K": 0.0,
    "pH": 7.0,
    "prediction": "Waiting",
    "confidence": 0.0,
    "is_live": False
}

# =====================================================
# UDP LISTENER & PROCESSOR
# =====================================================
def process_raw_udp_string(raw_str, port=None):
    global udp_data_count, last_udp_time

    temp, hum, rain, light, moisture = 0.0, 0.0, 0.0, 0, 0
    pH_value, N_value, P_value, K_value = 0.0, 0.0, 0.0, 0.0

    # 1. Key-Value format (e.g. TEMP:28.5,HUM:65,MOISTURE:70,PH:6.8,N:45,P:35,K:50)
    if ":" in raw_str:
        kv_dict = {}
        for item in raw_str.split(","):
            if ":" in item:
                k, v = item.split(":", 1)
                clean_k = k.strip("{} \"'").upper()
                clean_v = v.strip("{} \"'")
                kv_dict[clean_k] = clean_v

        for k, v in kv_dict.items():
            try:
                if k in ["TEMP", "TEMPERATURE"]: temp = float(v)
                elif k in ["HUM", "HUMIDITY"]: hum = float(v)
                elif k in ["RAIN", "RAINFALL"]: rain = float(v)
                elif k in ["LIGHT", "LDR", "LUX"]: light = int(float(v))
                elif k in ["MOISTURE", "MOIST"]: moisture = int(float(v))
                elif k in ["N", "NITROGEN"]: N_value = float(v)
                elif k in ["P", "PHOSPHORUS"]: P_value = float(v)
                elif k in ["K", "POTASSIUM"]: K_value = float(v)
                elif k in ["PH", "SOIL_PH"]:
                    try:
                        pH_value = float(v)
                    except ValueError:
                        v_upper = v.upper()
                        if "ACID" in v_upper: pH_value = 6.0
                        elif "BASE" in v_upper or "ALKALINE" in v_upper: pH_value = 8.0
                        else: pH_value = 7.0
            except Exception as parse_e:
                print(f"  ⚠ KV parse warning [{k}={v}]: {parse_e}")
    else:
        # 2. Positional CSV format
        parts = [p.strip() for p in raw_str.split(",")]
        if len(parts) >= 5:
            try: temp = float(parts[0])
            except ValueError: print(f"  ⚠ CSV temp parse failed: {parts[0]}")
            try: hum = float(parts[1])
            except ValueError: print(f"  ⚠ CSV hum parse failed: {parts[1]}")
            try: light = int(float(parts[2]))
            except ValueError: print(f"  ⚠ CSV light parse failed: {parts[2]}")
            try: moisture = int(float(parts[3]))
            except ValueError: print(f"  ⚠ CSV moisture parse failed: {parts[3]}")

        if len(parts) >= 8:
            try:
                pH_value = float(parts[4])
                ph_idx = 4
            except ValueError:
                ph_str = parts[4].upper()
                if "ACID" in ph_str: pH_value = 6.0
                elif "BASE" in ph_str or "ALKALINE" in ph_str: pH_value = 8.0
                else: pH_value = 7.0
                ph_idx = 4

            try: N_value = float(parts[ph_idx + 1])
            except (ValueError, IndexError): pass
            try: P_value = float(parts[ph_idx + 2])
            except (ValueError, IndexError): pass
            try: K_value = float(parts[ph_idx + 3])
            except (ValueError, IndexError): pass

    # Bounds check
    temp = temp if 0 <= temp <= 100 else 0.0
    hum = hum if 0 <= hum <= 100 else 0.0
    light = max(0, light)
    moisture = moisture if 0 <= moisture <= 100 else 0
    pH_value = pH_value if 0 <= pH_value <= 14 else 0.0
    N_value = max(0.0, N_value)
    P_value = max(0.0, P_value)
    K_value = max(0.0, K_value)

    # ML Soil Prediction
    predicted_label = "Optimal"
    confidence = 90.0
    try:
        import pandas as pd
        ldr_pct = float(light) if light <= 100.0 else min(100.0, max(0.0, (light / 1023.0) * 100.0))
        input_data = pd.DataFrame([[temp, hum, rain, ldr_pct, moisture]], columns=[
            "Temperature_C", "Humidity_percent", "Rain", "LDR_percent", "Moisture_percent"
        ])

        input_scaled = soil_scaler.transform(input_data)
        prediction = soil_model.predict(input_scaled)
        proba = soil_model.predict_proba(input_scaled)

        predicted_label = str(soil_label_encoder.inverse_transform(prediction)[0])
        confidence = float(np.max(proba) * 100)
    except Exception as ml_e:
        print(f"  ⚠ ML Prediction warning: {ml_e}", flush=True)

    # Update global data & write live_data.json
    with data_lock:
        last_udp_time = time.time()
        udp_data_count += 1
        latest_data.update({
            "temp": float(round(temp, 1)),
            "hum": float(round(hum, 1)),
            "rain": float(round(rain, 1)),
            "light": int(light),
            "ldr": float(round(ldr_pct, 1)),
            "moisture": int(moisture),
            "N": float(round(N_value, 1)),
            "P": float(round(P_value, 1)),
            "K": float(round(K_value, 1)),
            "pH": float(round(pH_value, 2)),
            "prediction": str(predicted_label),
            "confidence": float(round(confidence, 2)),
            "is_live": True
        })
        
        # Sync with live_data.json
        try:
            with open("live_data.json", "w") as f:
                json.dump({
                    "TEMP": float(round(temp, 1)),
                    "HUM": float(round(hum, 1)),
                    "RAIN": float(round(rain, 1)),
                    "LDR": float(round(ldr_pct, 1)),
                    "MOISTURE": float(round(moisture, 1)),
                    "N": float(round(N_value, 1)),
                    "P": float(round(P_value, 1)),
                    "K": float(round(K_value, 1)),
                    "PH": float(round(pH_value, 2))
                }, f)
        except Exception as json_e:
            pass

    if udp_data_count % 5 == 1:
        print(f"📡 Received {udp_data_count} UDP packets (Port {port}) - Temp={temp}°C, Hum={hum}%, pH={pH_value}", flush=True)

def listen_on_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("", port))
        print(f"✅ UDP Receiver Started on port {port}", flush=True)
    except Exception as e:
        print(f"❌ Failed to bind UDP port {port}: {e}", flush=True)
        return

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            raw_str = data.decode("utf-8", errors="ignore").strip()
            print(f"\n📡 RAW UDP RECEIVED on port {port} from {addr[0]}:{addr[1]} -> '{raw_str}'", flush=True)
            process_raw_udp_string(raw_str, port)
        except Exception as e:
            print(f"❌ UDP Error on port {port}: {e}", flush=True)

def udp_listener():
    threading.Thread(target=listen_on_port, args=(4210,), daemon=True).start()
    threading.Thread(target=listen_on_port, args=(5005,), daemon=True).start()

udp_listener()

# =====================================================
# IMAGE PREPROCESS
# =====================================================
def preprocess_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)

    image_array = np.asarray(image)
    normalized = (image_array.astype(np.float32) / 127.5) - 1

    data = np.ndarray((1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized
    return data

# =====================================================
# COMBINED AI ANALYSIS
# =====================================================
def generate_combined_ai(disease_name):
    with data_lock:
        soil_snapshot = latest_data.copy()

    prompt = f"""
    Smart Agriculture Analysis Report:

    Soil Status: {soil_snapshot['prediction']}
    Nitrogen: {soil_snapshot['N']}
    Phosphorus: {soil_snapshot['P']}
    Potassium: {soil_snapshot['K']}
    Moisture: {soil_snapshot['moisture']}
    Temperature: {soil_snapshot['temp']}
    Humidity: {soil_snapshot['hum']}

    Fruit Disease Detected: {disease_name}

    Provide:
    1. Overall farm health analysis
    2. Fertilizer recommendation
    3. Soil improvement strategy
    4. Disease treatment plan
    5. Crop growth optimization advice
    """

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

# =====================================================
# CHATBOT FUNCTION
# =====================================================
def chatbot_response(user_message):
    prompt = f"""
    You are an expert AI Agriculture Assistant.
    Answer clearly and practically.

    User Question:
    {user_message}
    """

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Chatbot Error: {str(e)}"

# =====================================================
# ROUTES
# =====================================================
@app.route("/hub")
def hub():
    """AgroAI Hub — two-card dashboard served over HTTP so fetch() works."""
    return render_template("hub.html")

@app.route("/", methods=["GET", "POST"])

def dashboard():
    fruit_result = None
    fruit_confidence = None
    image_path = None

    if request.method == "POST":
        file = request.files.get("image")

        if file and file.filename != "":
            image_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(image_path)

            data = preprocess_image(image_path)
            prediction = fruit_model.predict(data)

            idx = np.argmax(prediction)
            fruit_result = CLASS_NAMES[idx]
            fruit_confidence = float(prediction[0][idx]) * 100

    return render_template(
        "index.html",
        fruit_prediction=fruit_result,
        fruit_confidence=fruit_confidence,
        image_path=image_path
    )

@app.route("/api/predict_disease", methods=["POST"])
def api_predict_disease():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        image_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(image_path)

        data = preprocess_image(image_path)
        prediction = fruit_model.predict(data)

        idx = np.argmax(prediction)
        fruit_result = CLASS_NAMES[idx]
        fruit_confidence = float(prediction[0][idx]) * 100

        advice = generate_combined_ai(fruit_result)

        return jsonify({
            "status": "success",
            "prediction": fruit_result,
            "confidence": round(fruit_confidence, 2),
            "image_url": f"/{image_path.replace('\\', '/')}",
            "ai_advice": advice
        }), 200
    except Exception as e:
        print(f"❌ Disease prediction error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/predict_soil", methods=["POST"])
def api_predict_soil():
    try:
        req = request.json or {}
        n_val = float(req.get('N', 45))
        p_val = float(req.get('P', 35))
        k_val = float(req.get('K', 50))
        temp = float(req.get('temp', 25))
        hum = float(req.get('hum', 65))
        rain = float(req.get('rain', 0))
        ldr_pct = light if light <= 100.0 else min(100.0, max(0.0, (light / 1023.0) * 100.0))
        import pandas as pd
        input_data = pd.DataFrame([[temp, hum, rain, ldr_pct, moist]], columns=[
            "Temperature_C", "Humidity_percent", "Rain", "LDR_percent", "Moisture_percent"
        ])
        input_scaled = soil_scaler.transform(input_data)
        prediction = soil_model.predict(input_scaled)
        proba = soil_model.predict_proba(input_scaled)

        predicted_label = soil_label_encoder.inverse_transform(prediction)[0]
        confidence = float(np.max(proba) * 100)

        return jsonify({
            "status": "success",
            "prediction": predicted_label,
            "confidence": round(confidence, 2)
        }), 200
    except Exception as e:
        print(f"❌ Soil prediction error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/combined_ai", methods=["POST"])
def combined_ai():
    disease = request.json.get("disease")
    advice = generate_combined_ai(disease)
    return jsonify({"advice": advice})

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    reply = chatbot_response(user_message)
    return jsonify({"reply": reply})

@app.route("/data")
def get_data():
    try:
        # BUG FIX #4: latest_data was mutated ("is_live" = False) while holding the
        # lock AND then jsonify was called inside the lock — jsonify serialises lazily,
        # so the lock would be released before serialisation finished.
        # Fix: copy data under the lock, release the lock, then build the response.
        with data_lock:
            snapshot = dict(latest_data)
            if time.time() - last_udp_time > 25.0:
                snapshot["is_live"] = False
        response = jsonify(snapshot)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response, 200
    except Exception as e:
        print(f"❌ Error in /data endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/status", methods=["GET"])
def api_status():
    """Lightweight health-check for the hub dashboard."""
    with data_lock:
        live = latest_data.get("is_live", False)
        if time.time() - last_udp_time > 25.0:
            live = False
    return jsonify({
        "status": "ok",
        "is_live": live,
        "udp_packets": udp_data_count
    }), 200

@app.route("/api/send_test_packet", methods=["POST", "GET"])
def send_test_packet():
    try:
        import random
        temp = round(25.0 + random.uniform(-3, 5), 1)
        hum = round(65.0 + random.uniform(-10, 15), 1)
        light = random.randint(400, 750)
        moist = random.randint(55, 80)
        n_val = round(45.0 + random.uniform(-10, 15), 1)
        p_val = round(35.0 + random.uniform(-10, 15), 1)
        k_val = round(50.0 + random.uniform(-10, 15), 1)

        test_str = f"TEMP:{temp},HUM:{hum},LDR:{light},MOISTURE:{moist},PH:6.8,N:{n_val},P:{p_val},K:{k_val}"

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(test_str.encode('utf-8'), ('127.0.0.1', 4210))
        sock.close()

        return jsonify({"status": "success", "message": "Test UDP packet sent to port 4210", "packet": test_str}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 AI Smart Agriculture System Started")
    print("="*60)
    print("📡 UDP Listener: Port 4210 (Waiting for sensor data)")
    print("🌐 Flask Server: http://0.0.0.0:5000")
    print("📊 Data Endpoint: /data (JSON)")
    print("⚙️  Test Data Generator: Enabled (Fallback if UDP inactive)")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)