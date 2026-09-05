
import streamlit as st
import pandas as pd
import joblib
import json
import os
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
# LOAD MODEL
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
# READ LIVE DATA
# BUG FIX #7: open("live_data.json") uses a relative path which resolves to
# whatever the CWD is at runtime — can fail when launched from a different
# directory.  Use the script's own directory as the base.
# BUG FIX #8: bare "except: return None" silently swallowed ALL errors
# (JSON decode errors, permission errors, etc.).  Now logs the actual problem.
# ============================================================

def read_live_data():

    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "live_data.json")

    if not os.path.exists(json_path):
        return None

    try:
        with open(json_path, "r") as file:
            return json.load(file)

    except json.JSONDecodeError as e:
        print(f"live_data.json is not valid JSON: {e}")
        return None

    except Exception as e:
        print(f"Error reading live_data.json: {e}")
        return None


# ============================================================
# HEADER
# ============================================================

st.title(
    "🍅 Smart Tomato Crop Health Monitoring"
)

st.markdown(
    "### Real-Time Sensor Monitoring & XGBoost Prediction"
)

st.divider()


# ============================================================
# READ SENSOR DATA
# ============================================================

data = read_live_data()


if data is None:

    st.warning(
        "⏳ Waiting for live sensor data..."
    )

    st.info(
        "Make sure the UDP receiver is running "
        "and receiving ESP32 data."
    )

    time.sleep(2)

    st.rerun()


# ============================================================
# SENSOR VALUES
# ============================================================

temperature = float(
    data.get("TEMP", 0)
)

humidity = float(
    data.get("HUM", 0)
)

rain = float(
    data.get("RAIN", 0)
)

ldr = float(
    data.get("LDR", 0)
)

moisture = float(
    data.get("MOISTURE", 0)
)


# ============================================================
# LIVE SENSOR DASHBOARD
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
        f"{rain:.1f}"
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
# CREATE INPUT FOR MODEL
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
# SCALE DATA
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

probabilities = model.predict_proba(
    input_scaled
)


predicted_label = label_encoder.inverse_transform(
    prediction
)[0]


# ============================================================
# PREDICTION RESULT
# ============================================================

st.subheader(
    "🤖 Crop Health Prediction"
)


if predicted_label == "Low":

    st.error(
        "🔴 LOW"
    )

    st.write(
        "Crop condition requires attention."
    )


elif predicted_label == "Medium":

    st.warning(
        "🟡 MEDIUM"
    )

    st.write(
        "Crop condition is moderate."
    )


else:

    st.success(
        "🟢 HIGH"
    )

    st.write(
        "Crop condition is favorable."
    )


# ============================================================
# PROBABILITY
# ============================================================

st.subheader(
    "📊 Prediction Confidence"
)


prob_df = pd.DataFrame({

    "Condition": label_encoder.classes_,

    "Probability": probabilities[0] * 100

})


p1, p2, p3 = st.columns(3)


with p1:

    st.metric(
        "LOW",
        f"{prob_df.iloc[0]['Probability']:.2f}%"
    )


with p2:

    st.metric(
        "MEDIUM",
        f"{prob_df.iloc[1]['Probability']:.2f}%"
    )


with p3:

    st.metric(
        "HIGH",
        f"{prob_df.iloc[2]['Probability']:.2f}%"
    )


# ============================================================
# SENSOR TABLE
# ============================================================

st.divider()

st.subheader(
    "📋 Current Sensor Readings"
)


sensor_df = pd.DataFrame({

    "Sensor": [
        "Temperature",
        "Humidity",
        "Rain",
        "LDR",
        "Soil Moisture"
    ],

    "Value": [
        f"{temperature:.1f} °C",
        f"{humidity:.1f} %",
        f"{rain:.1f}",
        f"{ldr:.1f} %",
        f"{moisture:.1f} %"
    ]

})


st.dataframe(
    sensor_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# STATUS
# ============================================================

st.divider()

st.success(
    "🟢 LIVE SYSTEM ACTIVE"
)


# ============================================================
# AUTO UPDATE
# ============================================================

time.sleep(2)

st.rerun()

