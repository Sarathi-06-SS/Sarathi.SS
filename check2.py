
import streamlit as st
import pandas as pd
import numpy as np
import socket
import joblib
import os
import time
import certifi

# ============================================================
# FIX: SSL Certificate Verification
# ============================================================
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# ============================================================
# NEW Gemini SDK (google-genai)
# ============================================================
from google import genai


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart Tomato Crop Health Monitoring",
    page_icon="🍅",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #f5f7fa;
}

.title {
    font-size: 38px;
    font-weight: 700;
    color: #d32f2f;
    text-align: center;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #555;
    font-size: 17px;
    margin-bottom: 25px;
}

.section-title {
    font-size: 24px;
    font-weight: 650;
    color: #222;
    margin-top: 20px;
    margin-bottom: 12px;
}

.status-box {
    padding: 15px;
    border-radius: 10px;
    background-color: #ffffff;
    border: 1px solid #ddd;
    margin-bottom: 10px;
}

.prediction-box {
    padding: 25px;
    border-radius: 15px;
    background-color: #ffffff;
    border: 2px solid #ddd;
    text-align: center;
    margin-top: 15px;
}

.chat-box {
    padding: 15px;
    border-radius: 10px;
    background-color: white;
    border: 1px solid #ddd;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

# Set GEMINI_API_KEY in the environment before starting the app.
# Generate a key at:
# https://aistudio.google.com/app/apikey

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-3.5-flash-lite"

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# FILE NAMES
# ============================================================

MODEL_FILE = "quantum_xgboost_model.pkl"
SCALER_FILE = "scaler.pkl"
ENCODER_FILE = "label_encoder.pkl"


# ============================================================
# UDP SETTINGS
# ============================================================

UDP_IP = "0.0.0.0"
UDP_PORT = 5005


# ============================================================
# LOAD ML MODEL
# ============================================================

@st.cache_resource
def load_ml_model():

    try:
        model = joblib.load(MODEL_FILE)
        scaler = joblib.load(SCALER_FILE)
        label_encoder = joblib.load(ENCODER_FILE)

        return model, scaler, label_encoder

    except Exception as e:

        st.error(
            f"Unable to load ML model files.\n\n"
            f"Required files:\n"
            f"- {MODEL_FILE}\n"
            f"- {SCALER_FILE}\n"
            f"- {ENCODER_FILE}\n\n"
            f"Error: {e}"
        )

        return None, None, None


model, scaler, label_encoder = load_ml_model()


# ============================================================
# UDP SOCKET
# ============================================================

@st.cache_resource
def create_udp_socket():

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_BROADCAST,
            1
        )

        sock.bind(
            (UDP_IP, UDP_PORT)
        )

        sock.settimeout(0.1)

        return sock

    except Exception as e:

        st.error(
            f"UDP socket error: {e}"
        )

        return None


udp_socket = create_udp_socket()


# ============================================================
# UDP PACKET PARSER
# ============================================================

def parse_udp_packet(packet):

    try:

        packet = packet.strip()

        values = {}

        parts = packet.split(",")

        for item in parts:

            key, value = item.split(":")

            values[key.strip()] = float(
                value.strip()
            )

        required_keys = [
            "TEMP",
            "HUM",
            "RAIN",
            "LDR",
            "MOISTURE"
        ]

        for key in required_keys:

            if key not in values:
                return None

        sensor_data = {

            "Temperature_C":
                float(values["TEMP"]),

            "Humidity_percent":
                float(values["HUM"]),

            "Rain":
                float(values["RAIN"]),

            "LDR_percent":
                float(values["LDR"]),

            "Moisture_percent":
                float(values["MOISTURE"])

        }

        return sensor_data

    except Exception:

        return None


# ============================================================
# RECEIVE UDP PACKET
# ============================================================

def receive_udp_packet():

    if udp_socket is None:
        return None

    latest_data = None

    try:

        while True:

            try:

                data, address = udp_socket.recvfrom(1024)

                packet = data.decode(
                    "utf-8",
                    errors="ignore"
                )

                parsed = parse_udp_packet(packet)

                if parsed is not None:

                    latest_data = parsed

            except socket.timeout:

                break

            except BlockingIOError:

                break

    except Exception:

        return None

    return latest_data


# ============================================================
# ML PREDICTION
# ============================================================

def predict_crop_health(sensor_data):

    feature_order = [

        "Temperature_C",
        "Humidity_percent",
        "Rain",
        "LDR_percent",
        "Moisture_percent"

    ]

    input_df = pd.DataFrame(
        [[sensor_data[col] for col in feature_order]],
        columns=feature_order
    )

    try:

        # Keep scaler because the saved training pipeline
        # uses the scaler.

        scaled_data = scaler.transform(
            input_df
        )

        prediction = model.predict(
            scaled_data
        )

        probabilities = model.predict_proba(
            scaled_data
        )[0]

        predicted_label = label_encoder.inverse_transform(
            prediction
        )[0]

        return (
            predicted_label,
            probabilities
        )

    except Exception as e:

        st.error(
            f"Prediction error: {e}"
        )

        return None, None


# ============================================================
# INITIALIZE SESSION STATE
# ============================================================

if "mode" not in st.session_state:
    st.session_state.mode = "Live"

if "sensor_data" not in st.session_state:
    st.session_state.sensor_data = None

if "predicted_label" not in st.session_state:
    st.session_state.predicted_label = None

if "probabilities" not in st.session_state:
    st.session_state.probabilities = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">🍅 Smart Tomato Crop Health Monitoring</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'IoT Sensor Monitoring • XGBoost Prediction • Gemini AI Recommendation'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# MODE SELECTION
# ============================================================

col1, col2 = st.columns(2)

with col1:

    if st.button(
        "🔴 LIVE PREDICTION",
        use_container_width=True
    ):

        st.session_state.mode = "Live"


with col2:

    if st.button(
        "🟢 USER INPUT PREDICTION",
        use_container_width=True
    ):

        st.session_state.mode = "User"


st.divider()


# ============================================================
# LIVE MODE
# ============================================================

if st.session_state.mode == "Live":

    st.markdown(
        '<div class="section-title">'
        '🔴 Live ESP32 Sensor Monitoring'
        '</div>',
        unsafe_allow_html=True
    )

    live_data = receive_udp_packet()

    if live_data is not None:

        st.session_state.sensor_data = live_data

        st.success(
            "ESP32 UDP data received successfully."
        )

        sensor_data = live_data

        # --------------------------------------------
        # SENSOR DISPLAY
        # --------------------------------------------

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "🌡 Temperature",
            f"{sensor_data['Temperature_C']:.1f} °C"
        )

        c2.metric(
            "💧 Humidity",
            f"{sensor_data['Humidity_percent']:.1f} %"
        )

        c3.metric(
            "🌧 Rain",
            f"{sensor_data['Rain']:.1f} %"
        )

        c4.metric(
            "☀ LDR",
            f"{sensor_data['LDR_percent']:.1f} %"
        )

        c5.metric(
            "🌱 Soil Moisture",
            f"{sensor_data['Moisture_percent']:.1f} %"
        )

        # --------------------------------------------
        # PREDICTION
        # --------------------------------------------

        if model is not None:

            predicted_label, probabilities = predict_crop_health(
                sensor_data
            )

            if predicted_label is not None:

                st.session_state.predicted_label = predicted_label
                st.session_state.probabilities = probabilities

    else:

        st.warning(
            "Waiting for ESP32 UDP sensor data..."
        )

        st.info(
            f"Listening on UDP port {UDP_PORT}"
        )

        sensor_data = st.session_state.sensor_data


# ============================================================
# USER INPUT MODE
# ============================================================

else:

    st.markdown(
        '<div class="section-title">'
        '🟢 Manual Sensor Input'
        '</div>',
        unsafe_allow_html=True
    )

    st.info(
        "Enter the current tomato field sensor values."
    )

    c1, c2 = st.columns(2)

    with c1:

        temperature = st.number_input(
            "🌡 Temperature (°C)",
            min_value=-10.0,
            max_value=60.0,
            value=29.5,
            step=0.1
        )

        humidity = st.number_input(
            "💧 Humidity (%)",
            min_value=0.0,
            max_value=100.0,
            value=65.0,
            step=0.1
        )

        rain = st.number_input(
            "🌧 Rain (%)",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=1.0
        )

    with c2:

        ldr = st.number_input(
            "☀ LDR / Light (%)",
            min_value=0.0,
            max_value=100.0,
            value=75.0,
            step=1.0
        )

        moisture = st.number_input(
            "🌱 Soil Moisture (%)",
            min_value=0.0,
            max_value=100.0,
            value=55.0,
            step=1.0
        )

    sensor_data = {

        "Temperature_C":
            float(temperature),

        "Humidity_percent":
            float(humidity),

        "Rain":
            float(rain),

        "LDR_percent":
            float(ldr),

        "Moisture_percent":
            float(moisture)
    }

    st.session_state.sensor_data = sensor_data

    if st.button(
        "🔍 PREDICT CROP HEALTH",
        use_container_width=True
    ):

        if model is not None:

            predicted_label, probabilities = predict_crop_health(
                sensor_data
            )

            if predicted_label is not None:

                st.session_state.predicted_label = predicted_label
                st.session_state.probabilities = probabilities

                st.success(
                    "Crop health prediction completed."
                )


# ============================================================
# DISPLAY SENSOR TABLE
# ============================================================

if sensor_data is not None:

    st.markdown(
        '<div class="section-title">'
        '📊 Sensor Data'
        '</div>',
        unsafe_allow_html=True
    )

    sensor_table = pd.DataFrame({

        "Parameter": [
            "Temperature",
            "Humidity",
            "Rain",
            "LDR / Light",
            "Soil Moisture"
        ],

        "Value": [

            f"{sensor_data['Temperature_C']:.2f} °C",

            f"{sensor_data['Humidity_percent']:.2f} %",

            f"{sensor_data['Rain']:.2f} %",

            f"{sensor_data['LDR_percent']:.2f} %",

            f"{sensor_data['Moisture_percent']:.2f} %"

        ]

    })

    st.dataframe(
        sensor_table,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# PREDICTION RESULT
# ============================================================

if (
    st.session_state.predicted_label is not None
    and st.session_state.probabilities is not None
):

    predicted_label = st.session_state.predicted_label
    probabilities = st.session_state.probabilities

    st.markdown(
        '<div class="section-title">'
        '🤖 XGBoost Crop Health Prediction'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="prediction-box">',
        unsafe_allow_html=True
    )

    st.subheader(
        f"Predicted Crop Health: {predicted_label}"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    st.write("### Prediction Probability")

    classes = label_encoder.classes_

    for i, class_name in enumerate(classes):

        probability_value = float(
            probabilities[i]
        )

        # IMPORTANT:
        # Streamlit st.progress() requires a Python float.

        progress_value = float(
            max(
                0.0,
                min(
                    probability_value,
                    1.0
                )
            )
        )

        st.write(
            f"**{class_name}: "
            f"{probability_value * 100:.2f}%**"
        )

        st.progress(
            progress_value
        )


# ============================================================
# GEMINI AI FARMER REPORT
# ============================================================

if (
    sensor_data is not None
    and st.session_state.predicted_label is not None
):

    st.divider()

    st.markdown(
        '<div class="section-title">'
        '🌾 Gemini AI Farmer Recommendation'
        '</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🧠 GENERATE AI CULTIVATION REPORT",
        use_container_width=True
    ):

        try:

            predicted_label = st.session_state.predicted_label

            probabilities = st.session_state.probabilities

            probability_text = ""

            for i, class_name in enumerate(
                label_encoder.classes_
            ):

                probability_text += (
                    f"{class_name}: "
                    f"{float(probabilities[i]) * 100:.2f}%\n"
                )

            prompt = f"""
You are an agricultural advisory assistant specializing
in tomato crop cultivation.

Analyze the following real-time tomato field information.

SENSOR DATA
-----------
Temperature: {sensor_data['Temperature_C']:.2f} °C
Humidity: {sensor_data['Humidity_percent']:.2f} %
Rainfall: {sensor_data['Rain']:.2f} %
LDR / Light: {sensor_data['LDR_percent']:.2f} %
Soil Moisture: {sensor_data['Moisture_percent']:.2f} %

MACHINE LEARNING RESULT
-----------------------
Predicted Crop Health: {predicted_label}

Prediction Probabilities:
{probability_text}

Generate a practical farmer-oriented tomato cultivation report.

The report must contain exactly these sections:

1. Overall Crop Condition
2. Sensor Condition Analysis
3. Irrigation Recommendation
4. Soil Moisture Recommendation
5. Temperature Recommendation
6. Humidity Recommendation
7. Rainfall Recommendation
8. Light / LDR Recommendation
9. Fertilizer and Nutrient Suggestion
10. Disease and Pest Prevention
11. Immediate Actions for Farmer
12. Short-Term Cultivation Plan
13. Final Farmer Recommendation

Important instructions:

- Give practical and easy-to-understand recommendations.
- Relate recommendations to the provided sensor values.
- Use the XGBoost prediction as supporting information.
- Do not claim that a specific disease is definitely present only from
  temperature, humidity, rainfall, light, or soil moisture.
- If disease risk is suggested, clearly describe it as a possible risk
  and recommend visual inspection.
- Avoid unrealistic or unsafe agricultural recommendations.
- Mention when field inspection is required.
- Keep the report concise but useful for farmers.
"""

            with st.spinner(
                "Gemini AI is preparing the farmer recommendation..."
            ):

                response = gemini_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt
                )

            if response and response.text:

                st.markdown(
                    response.text
                )

            else:

                st.warning(
                    "Gemini did not return a report."
                )

        except Exception as e:

            st.error(
                f"Gemini AI report error: {e}"
            )


# ============================================================
# GEMINI FARMER CHATBOT
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">'
    '💬 Gemini AI Farmer Assistant'
    '</div>',
    unsafe_allow_html=True
)

st.write(
    "Ask questions about tomato cultivation, irrigation, "
    "soil moisture, fertilizer, environmental conditions, "
    "or the current prediction."
)


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.chat_history:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# CHAT INPUT
# ============================================================

user_message = st.chat_input(
    "Ask the AI farmer assistant..."
)


if user_message:

    # --------------------------------------------
    # ADD USER MESSAGE
    # --------------------------------------------

    st.session_state.chat_history.append({

        "role": "user",

        "content": user_message

    })

    with st.chat_message("user"):

        st.markdown(
            user_message
        )

    # --------------------------------------------
    # BUILD CONTEXT
    # --------------------------------------------

    if sensor_data is not None:

        current_sensor_context = f"""
Current sensor readings:

Temperature:
{sensor_data['Temperature_C']:.2f} °C

Humidity:
{sensor_data['Humidity_percent']:.2f} %

Rain:
{sensor_data['Rain']:.2f} %

LDR / Light:
{sensor_data['LDR_percent']:.2f} %

Soil Moisture:
{sensor_data['Moisture_percent']:.2f} %
"""

    else:

        current_sensor_context = (
            "No current sensor readings are available."
        )


    if st.session_state.predicted_label is not None:

        prediction_context = f"""
Current XGBoost crop health prediction:

{st.session_state.predicted_label}
"""

    else:

        prediction_context = (
            "No current XGBoost prediction is available."
        )


    chat_prompt = f"""
You are a smart agricultural assistant for tomato farmers.

Provide simple, practical and accurate answers.

{current_sensor_context}

{prediction_context}

Farmer's question:
{user_message}

Instructions:

- Answer specifically for tomato cultivation.
- Use the current sensor information when relevant.
- Use the ML prediction only as supporting information.
- Do not claim a disease is definitely present without appropriate
  visual or laboratory confirmation.
- Give actionable recommendations.
- If the question requires physical field inspection, clearly mention it.
- Avoid unnecessary technical language.
"""


    # --------------------------------------------
    # GENERATE GEMINI RESPONSE
    # --------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "AI is thinking..."
        ):

            try:

                response = gemini_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=chat_prompt
                )

                if response and response.text:

                    answer = response.text

                else:

                    answer = (
                        "Sorry, I could not generate a response."
                    )

            except Exception as e:

                answer = (
                    f"Gemini chatbot error: {e}"
                )

        st.markdown(
            answer
        )


    # --------------------------------------------
    # SAVE RESPONSE
    # --------------------------------------------

    st.session_state.chat_history.append({

        "role": "assistant",

        "content": answer

    })


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "🍅 System Information"
    )

    st.write(
        f"**Mode:** {st.session_state.mode}"
    )

    st.write(
        f"**UDP Port:** {UDP_PORT}"
    )

    st.write(
        "**ML Algorithm:** XGBoost"
    )

    st.write(
        "**AI Model:** Gemini 2.5 Flash Lite"
    )

    st.divider()

    st.subheader(
        "Required Files"
    )

    st.write(
        f"✓ {MODEL_FILE}"
    )

    st.write(
        f"✓ {SCALER_FILE}"
    )

    st.write(
        f"✓ {ENCODER_FILE}"
    )

    st.divider()

    st.subheader(
        "ESP32 UDP Format"
    )

    st.code(
        "TEMP:29.5,HUM:65.0,"
        "RAIN:20,LDR:75,MOISTURE:55"
    )

    st.divider()

    if st.button(
        "🗑 Clear Chat",
        use_container_width=True
    ):

        st.session_state.chat_history = []

        st.rerun()


# ============================================================
# LIVE MODE AUTO REFRESH
# ============================================================

if st.session_state.mode == "Live":

    time.sleep(1)

    st.rerun()

