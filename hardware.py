import streamlit as st
import socket
import threading
import time
import pandas as pd
import joblib


# ============================================================
# STREAMLIT PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Tomato Crop Health Monitoring",
    page_icon="🍅",
    layout="wide"
)


# ============================================================
# UDP CONFIGURATION
# BUG FIX #5: Port was 5005, but main.py and the ESP32 use 4210.
#             Unified to 4210 so they share the same channel.
# ============================================================

UDP_IP = "0.0.0.0"
UDP_PORT = 4210


# ============================================================
# LOAD MACHINE LEARNING MODEL
# ============================================================

@st.cache_resource
def load_model():

    model = joblib.load(
        "quantum_xgboost_model.pkl"
    )

    scaler = joblib.load(
        "scaler.pkl"
    )

    label_encoder = joblib.load(
        "label_encoder.pkl"
    )

    return model, scaler, label_encoder


model, scaler, label_encoder = load_model()


# ============================================================
# GLOBAL LIVE SENSOR DATA
# ============================================================

if "sensor_data" not in st.session_state:

    st.session_state.sensor_data = {
        "TEMP": 0.0,
        "HUM": 0.0,
        "RAIN": 0.0,
        "LDR": 0.0,
        "MOISTURE": 0.0
    }


if "last_packet" not in st.session_state:
    st.session_state.last_packet = "Waiting for ESP32..."


if "last_time" not in st.session_state:
    st.session_state.last_time = 0


# ============================================================
# UDP RECEIVER
# ============================================================

def udp_receiver():

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    sock.bind(
        (UDP_IP, UDP_PORT)
    )

    print("========================================")
    print("UDP RECEIVER STARTED")
    print("========================================")
    print(f"Listening on UDP port: {UDP_PORT}")
    print("Waiting for ESP32 sensor data...")
    print("----------------------------------------")


    while True:

        try:

            data, addr = sock.recvfrom(1024)

            message = data.decode(
                "utf-8"
            ).strip()

            print("\nReceived from:")
            print(
                f"{addr[0]}:{addr[1]}"
            )

            print(
                "Raw Data:",
                message
            )


            # ------------------------------------------------
            # PARSE UDP DATA
            # BUG FIX #6: Code did key.split(":") without checking ":" exists,
            # and accessed values["TEMP"] etc. directly — any missing key caused
            # an unhandled KeyError that crashed the whole UDP thread permanently.
            # Fix: wrap parsing in try/except and use .get() with safe defaults.
            # ------------------------------------------------

            values = {}

            for item in message.split(","):
                if ":" in item:
                    key, value = item.split(":", 1)
                    values[key.strip().upper()] = value.strip()

            try:
                temperature = float(values.get("TEMP", 25.0))
            except ValueError:
                temperature = 25.0

            try:
                humidity = float(values.get("HUM", 65.0))
            except ValueError:
                humidity = 65.0

            try:
                rainfall = float(values.get("RAIN", 0.0))
            except ValueError:
                rainfall = 0.0

            try:
                ldr = float(values.get("LDR", 50.0))
            except ValueError:
                ldr = 50.0

            try:
                moisture = float(values.get("MOISTURE", 70.0))
            except ValueError:
                moisture = 70.0


            # ------------------------------------------------
            # UPDATE LIVE DATA
            # ------------------------------------------------

            st.session_state.sensor_data = {

                "TEMP": temperature,

                "HUM": humidity,

                "RAIN": rainfall,

                "LDR": ldr,

                "MOISTURE": moisture

            }


            st.session_state.last_packet = message

            st.session_state.last_time = time.time()


            # ------------------------------------------------
            # TERMINAL DISPLAY
            # ------------------------------------------------

            print("----------------------------------------")

            print(
                f"Temperature : "
                f"{temperature:.1f} °C"
            )

            print(
                f"Humidity    : "
                f"{humidity:.1f} %"
            )

            print(
                f"Rainfall    : "
                f"{rainfall:.1f} %"
            )

            print(
                f"LDR         : "
                f"{ldr:.1f} %"
            )

            print(
                f"Moisture    : "
                f"{moisture:.1f} %"
            )

            print("----------------------------------------")


        except Exception as e:

            print(
                "UDP Packet Error:",
                e
            )


# ============================================================
# START UDP THREAD ONLY ONCE
# ============================================================

if "udp_started" not in st.session_state:

    udp_thread = threading.Thread(
        target=udp_receiver,
        daemon=True
    )

    udp_thread.start()

    st.session_state.udp_started = True


# ============================================================
# HEADER
# ============================================================

st.title(
    "🍅 Smart Tomato Crop Health Monitoring"
)

st.write(
    "Real-time ESP32 sensor monitoring "
    "using UDP communication and XGBoost prediction."
)


st.divider()


# ============================================================
# GET CURRENT SENSOR VALUES
# ============================================================

temperature = st.session_state.sensor_data["TEMP"]

humidity = st.session_state.sensor_data["HUM"]

rainfall = st.session_state.sensor_data["RAIN"]

ldr = st.session_state.sensor_data["LDR"]

moisture = st.session_state.sensor_data["MOISTURE"]


# ============================================================
# SENSOR DASHBOARD
# ============================================================

st.subheader("📡 Live Sensor Data")


col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "🌡 Temperature",
        f"{temperature:.1f} °C"
    )


with col2:

    st.metric(
        "💧 Humidity",
        f"{humidity:.1f} %"
    )


with col3:

    st.metric(
        "🌧 Rain",
        f"{rainfall:.1f}"
    )


with col4:

    st.metric(
        "☀ LDR",
        f"{ldr:.1f} %"
    )


with col5:

    st.metric(
        "🌱 Moisture",
        f"{moisture:.1f} %"
    )


st.divider()


# ============================================================
# MACHINE LEARNING PREDICTION
# ============================================================

input_data = pd.DataFrame({

    "Temperature_C": [
        temperature
    ],

    "Humidity_percent": [
        humidity
    ],

    "Rain": [
        rainfall
    ],

    "LDR_percent": [
        ldr
    ],

    "Moisture_percent": [
        moisture
    ]

})


# ============================================================
# SCALE LIVE DATA
# ============================================================

input_scaled = scaler.transform(
    input_data
)


# ============================================================
# XGBOOST PREDICTION
# ============================================================

prediction = model.predict(
    input_scaled
)

probability = model.predict_proba(
    input_scaled
)


predicted_label = label_encoder.inverse_transform(
    prediction
)[0]


# ============================================================
# DISPLAY PREDICTION
# ============================================================

st.subheader(
    "🤖 XGBoost Crop Condition Prediction"
)


if predicted_label == "Low":

    st.error(
        "🔴 LOW CROP CONDITION"
    )

    st.write(
        "The current sensor conditions indicate "
        "a low crop condition."
    )


elif predicted_label == "Medium":

    st.warning(
        "🟡 MEDIUM CROP CONDITION"
    )

    st.write(
        "The current sensor conditions indicate "
        "a moderate crop condition."
    )


else:

    st.success(
        "🟢 HIGH CROP CONDITION"
    )

    st.write(
        "The current sensor conditions indicate "
        "a favorable crop condition."
    )


# ============================================================
# PROBABILITY
# ============================================================

st.subheader(
    "📊 Prediction Probability"
)


probability_df = pd.DataFrame({

    "Condition": label_encoder.classes_,

    "Probability": probability[0] * 100

})


col1, col2, col3 = st.columns(3)


for index, row in probability_df.iterrows():

    with [
        col1,
        col2,
        col3
    ][index]:

        st.metric(
            row["Condition"],
            f"{row['Probability']:.2f}%"
        )


# ============================================================
# LIVE SENSOR TABLE
# ============================================================

st.divider()

st.subheader(
    "📋 Current Sensor Readings"
)


sensor_table = pd.DataFrame({

    "Parameter": [

        "Temperature",

        "Humidity",

        "Rainfall",

        "LDR",

        "Soil Moisture"

    ],

    "Value": [

        f"{temperature:.1f} °C",

        f"{humidity:.1f} %",

        f"{rainfall:.1f}",

        f"{ldr:.1f} %",

        f"{moisture:.1f} %"

    ]

})


st.dataframe(
    sensor_table,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# CONNECTION STATUS
# ============================================================

st.divider()

st.subheader(
    "📡 UDP Connection Status"
)


if st.session_state.last_time > 0:

    elapsed = (
        time.time()
        - st.session_state.last_time
    )


    if elapsed < 10:

        st.success(
            "🟢 ESP32 Connected — "
            f"Last packet {elapsed:.1f} seconds ago"
        )

    else:

        st.warning(
            "🟡 No recent packet received — "
            f"last packet {elapsed:.1f} seconds ago"
        )

else:

    st.info(
        "🔵 Waiting for ESP32 UDP data..."
    )


st.caption(
    f"UDP Server: {UDP_IP}:{UDP_PORT}"
)


# ============================================================
# AUTO REFRESH
# ============================================================

time.sleep(1)

st.rerun()