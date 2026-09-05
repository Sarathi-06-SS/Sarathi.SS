
import streamlit as st
import socket
import pandas as pd
import joblib
import time


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Tomato Crop Health Monitoring",
    page_icon="🍅",
    layout="wide"
)


# ============================================================
# UDP CONFIGURATION
# ============================================================

UDP_IP = "0.0.0.0"
UDP_PORT = 5005


# ============================================================
# LOAD TRAINED MODEL
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


# ============================================================
# LOAD MODEL SAFELY
# ============================================================

try:

    model, scaler, label_encoder = load_model()

except Exception as e:

    st.error(
        "❌ Model files could not be loaded."
    )

    st.code(
        str(e)
    )

    st.stop()


# ============================================================
# CREATE UDP SOCKET
# ============================================================

@st.cache_resource
def create_udp_socket():

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    # Allow broadcast reception
    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_BROADCAST,
        1
    )

    sock.bind(
        (
            UDP_IP,
            UDP_PORT
        )
    )

    # Non-blocking
    sock.settimeout(0.1)

    return sock


try:

    sock = create_udp_socket()

except OSError as e:

    st.error(
        f"❌ UDP port {UDP_PORT} is already in use."
    )

    st.code(
        str(e)
    )

    st.info(
        "Close any other Python program using UDP port 5005."
    )

    st.stop()


# ============================================================
# INITIAL SESSION STATE
# ============================================================

if "sensor_data" not in st.session_state:

    st.session_state.sensor_data = {

        "TEMP": 0.0,

        "HUM": 0.0,

        "RAIN": 0.0,

        "LDR": 0.0,

        "MOISTURE": 0.0
    }


if "connected" not in st.session_state:

    st.session_state.connected = False


if "last_packet" not in st.session_state:

    st.session_state.last_packet = ""


if "last_address" not in st.session_state:

    st.session_state.last_address = ""


if "last_update" not in st.session_state:

    st.session_state.last_update = 0.0


# ============================================================
# RECEIVE UDP PACKET
# ============================================================

def receive_udp_packet():

    latest_packet = None

    while True:

        try:

            data, address = sock.recvfrom(
                1024
            )

            message = data.decode(
                "utf-8",
                errors="ignore"
            ).strip()

            if message:

                latest_packet = (
                    message,
                    address
                )

        except socket.timeout:

            break

        except BlockingIOError:

            break

        except Exception as e:

            print(
                "UDP Receive Error:",
                e
            )

            break

    return latest_packet


# ============================================================
# PARSE UDP SENSOR DATA
# ============================================================

def parse_sensor_packet(message):

    try:

        values = {}

        for item in message.split(","):

            if ":" not in item:

                continue

            key, value = item.split(
                ":",
                1
            )

            key = key.strip().upper()

            value = value.strip()

            values[key] = value


        # Required fields
        required_fields = [
            "TEMP",
            "HUM",
            "RAIN",
            "LDR",
            "MOISTURE"
        ]


        for field in required_fields:

            if field not in values:

                raise ValueError(
                    f"Missing field: {field}"
                )


        temperature = float(
            values["TEMP"]
        )

        humidity = float(
            values["HUM"]
        )

        rain = float(
            values["RAIN"]
        )

        ldr = float(
            values["LDR"]
        )

        moisture = float(
            values["MOISTURE"]
        )


        return {

            "TEMP": temperature,

            "HUM": humidity,

            "RAIN": rain,

            "LDR": ldr,

            "MOISTURE": moisture

        }


    except Exception as e:

        print(
            "Packet Parsing Error:",
            e
        )

        return None


# ============================================================
# RECEIVE NEW DATA
# ============================================================

packet = receive_udp_packet()


if packet is not None:

    message, address = packet

    parsed_data = parse_sensor_packet(
        message
    )


    if parsed_data is not None:

        st.session_state.sensor_data = (
            parsed_data
        )

        st.session_state.connected = True

        st.session_state.last_packet = (
            message
        )

        st.session_state.last_address = (
            f"{address[0]}:{address[1]}"
        )

        st.session_state.last_update = (
            time.time()
        )


# ============================================================
# GET CURRENT SENSOR VALUES
# ============================================================

temperature = float(
    st.session_state.sensor_data["TEMP"]
)

humidity = float(
    st.session_state.sensor_data["HUM"]
)

rain = float(
    st.session_state.sensor_data["RAIN"]
)

ldr = float(
    st.session_state.sensor_data["LDR"]
)

moisture = float(
    st.session_state.sensor_data["MOISTURE"]
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "🍅 Smart Tomato Crop Health Monitoring"
)

st.markdown(
    "### Real-Time ESP32 UDP Sensor Monitoring & XGBoost Prediction"
)


st.divider()


# ============================================================
# CONNECTION STATUS
# ============================================================

status_col, packet_col = st.columns(
    [1, 2]
)


with status_col:

    if st.session_state.connected:

        elapsed = (
            time.time()
            - st.session_state.last_update
        )


        if elapsed <= 10:

            st.success(
                "🟢 ESP32 CONNECTED"
            )

        else:

            st.warning(
                "🟡 NO RECENT DATA"
            )

    else:

        st.info(
            "🔵 WAITING FOR ESP32"
        )


with packet_col:

    if st.session_state.last_packet:

        st.write(
            "**Last UDP Packet**"
        )

        st.code(
            st.session_state.last_packet
        )

    else:

        st.write(
            "**Last UDP Packet:** Waiting..."
        )


# ============================================================
# LIVE SENSOR DATA
# ============================================================

st.subheader(
    "📡 Live Sensor Data"
)


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
        f"{rain:.0f} %"
    )


with col4:

    st.metric(
        "☀ LDR",
        f"{ldr:.0f} %"
    )


with col5:

    st.metric(
        "🌱 Moisture",
        f"{moisture:.0f} %"
    )


st.divider()


# ============================================================
# MODEL INPUT
# ============================================================

input_data = pd.DataFrame({

    "Temperature_C": [
        temperature
    ],

    "Humidity_percent": [
        humidity
    ],

    "Rain": [
        rain
    ],

    "LDR_percent": [
        ldr
    ],

    "Moisture_percent": [
        moisture
    ]

})


# ============================================================
# SCALE INPUT
# ============================================================

try:

    input_scaled = scaler.transform(
        input_data
    )

except Exception as e:

    st.error(
        "❌ Error while scaling sensor data."
    )

    st.code(
        str(e)
    )

    st.stop()


# ============================================================
# XGBOOST PREDICTION
# ============================================================

try:

    prediction = model.predict(
        input_scaled
    )

    probability = model.predict_proba(
        input_scaled
    )

except Exception as e:

    st.error(
        "❌ XGBoost prediction failed."
    )

    st.code(
        str(e)
    )

    st.stop()


# ============================================================
# GET PREDICTED LABEL
# ============================================================

predicted_label = (
    label_encoder.inverse_transform(
        prediction
    )[0]
)


# ============================================================
# CROP CONDITION
# ============================================================

st.subheader(
    "🤖 XGBoost Crop Condition"
)


if predicted_label.upper() == "LOW":

    st.error(
        "🔴 LOW CROP CONDITION"
    )

    st.write(
        "Current environmental conditions "
        "indicate a low crop condition."
    )


elif predicted_label.upper() in [
    "MEDIUM",
    "MED"
]:

    st.warning(
        "🟡 MEDIUM CROP CONDITION"
    )

    st.write(
        "Current environmental conditions "
        "indicate a moderate crop condition."
    )


elif predicted_label.upper() == "HIGH":

    st.success(
        "🟢 HIGH CROP CONDITION"
    )

    st.write(
        "Current environmental conditions "
        "indicate a favorable crop condition."
    )


else:

    st.info(
        f"Prediction: {predicted_label}"
    )


# ============================================================
# PREDICTION PROBABILITY
# ============================================================

st.subheader(
    "📊 Prediction Probability"
)


probability_columns = st.columns(
    len(label_encoder.classes_)
)


for i, label in enumerate(
    label_encoder.classes_
):

    # IMPORTANT:
    # Convert NumPy float32 to Python float
    probability_value = float(
        probability[0][i]
    )


    # Convert to percentage
    percentage = float(
        probability_value * 100.0
    )


    # Streamlit progress requires Python float
    progress_value = float(
        max(
            0.0,
            min(
                probability_value,
                1.0
            )
        )
    )


    with probability_columns[i]:

        st.metric(
            label.upper(),
            f"{percentage:.2f}%"
        )


        st.progress(
            progress_value
        )


# ============================================================
# SENSOR DATA TABLE
# ============================================================

st.divider()

st.subheader(
    "📋 Current Sensor Readings"
)


sensor_table = pd.DataFrame({

    "Sensor": [

        "Temperature",

        "Humidity",

        "Rainfall",

        "LDR / Light",

        "Soil Moisture"

    ],

    "Value": [

        f"{temperature:.1f} °C",

        f"{humidity:.1f} %",

        f"{rain:.0f} %",

        f"{ldr:.0f} %",

        f"{moisture:.0f} %"

    ]

})


st.dataframe(
    sensor_table,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# RAW DATA / UDP INFORMATION
# ============================================================

st.divider()

st.subheader(
    "📡 UDP Communication"
)


udp_col1, udp_col2, udp_col3 = st.columns(3)


with udp_col1:

    st.metric(
        "UDP Port",
        str(UDP_PORT)
    )


with udp_col2:

    st.metric(
        "UDP Mode",
        "Broadcast"
    )


with udp_col3:

    if st.session_state.last_address:

        st.metric(
            "ESP32 Source",
            st.session_state.last_address
        )

    else:

        st.metric(
            "ESP32 Source",
            "Waiting..."
        )


# ============================================================
# LAST UPDATE
# ============================================================

if st.session_state.last_update > 0:

    update_time = time.strftime(
        "%H:%M:%S",
        time.localtime(
            st.session_state.last_update
        )
    )

    st.caption(
        f"Last sensor update: {update_time}"
    )


# ============================================================
# SYSTEM STATUS
# ============================================================

st.divider()

if st.session_state.connected:

    st.success(
        "🟢 LIVE SYSTEM ACTIVE"
    )

else:

    st.info(
        "🔵 SYSTEM READY — Waiting for ESP32 UDP data"
    )


# ============================================================
# AUTO REFRESH
# ============================================================

time.sleep(1)

st.rerun()

