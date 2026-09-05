
import streamlit as st
import pandas as pd
import joblib


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Tomato Crop Health Prediction",
    page_icon="🍅",
    layout="centered"
)


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


model, scaler, label_encoder = load_model()


# ============================================================
# HEADER
# ============================================================

st.title("🍅 Tomato Crop Health Prediction")

st.write(
    "Enter the sensor readings to predict the "
    "tomato crop condition."
)

st.divider()


# ============================================================
# SENSOR INPUTS
# ============================================================

st.subheader("🌱 Sensor Parameters")


temperature = st.number_input(
    "Temperature (°C)",
    min_value=0.0,
    max_value=50.0,
    value=29.4,
    step=0.1
)


humidity = st.number_input(
    "Humidity (%)",
    min_value=0.0,
    max_value=100.0,
    value=68.0,
    step=0.1
)


rain = st.number_input(
    "Rain",
    min_value=0.0,
    max_value=100.0,
    value=24.0,
    step=1.0
)


ldr = st.number_input(
    "LDR (%)",
    min_value=0.0,
    max_value=100.0,
    value=73.0,
    step=1.0
)


moisture = st.number_input(
    "Soil Moisture (%)",
    min_value=0.0,
    max_value=100.0,
    value=58.0,
    step=1.0
)


st.divider()


# ============================================================
# PREDICTION BUTTON
# ============================================================

if st.button(
    "🔍 Predict Crop Condition",
    use_container_width=True
):

    # --------------------------------------------------------
    # CREATE INPUT DATAFRAME
    # --------------------------------------------------------

    input_data = pd.DataFrame({

        "Temperature_C": [temperature],

        "Humidity_percent": [humidity],

        "Rain": [rain],

        "LDR_percent": [ldr],

        "Moisture_percent": [moisture]

    })


    # --------------------------------------------------------
    # SCALE INPUT
    # --------------------------------------------------------

    input_scaled = scaler.transform(
        input_data
    )


    # --------------------------------------------------------
    # PREDICTION
    # --------------------------------------------------------

    prediction = model.predict(
        input_scaled
    )


    probabilities = model.predict_proba(
        input_scaled
    )


    predicted_label = label_encoder.inverse_transform(
        prediction
    )[0]


    # ========================================================
    # DISPLAY RESULT
    # ========================================================

    st.subheader("📊 Prediction Result")


    if predicted_label == "Low":

        st.error(
            "🔴 Crop Condition: LOW"
        )

        st.write(
            "The sensor conditions indicate "
            "an unfavorable crop condition."
        )


    elif predicted_label == "Medium":

        st.warning(
            "🟡 Crop Condition: MEDIUM"
        )

        st.write(
            "The sensor conditions indicate "
            "a moderate crop condition."
        )


    else:

        st.success(
            "🟢 Crop Condition: HIGH"
        )

        st.write(
            "The sensor conditions indicate "
            "a favorable crop condition."
        )


    # ========================================================
    # PROBABILITY
    # ========================================================

    st.subheader("Prediction Probability")


    probability_data = pd.DataFrame({

        "Condition": label_encoder.classes_,

        "Probability": probabilities[0]

    })


    probability_data["Probability"] = (
        probability_data["Probability"] * 100
    )


    for index, row in probability_data.iterrows():

        st.write(
            f"**{row['Condition']}**: "
            f"{row['Probability']:.2f}%"
        )

        st.progress(
            float(row["Probability"] / 100)
        )


    # ========================================================
    # SENSOR VALUES
    # ========================================================

    st.subheader("Sensor Values Used")


    display_data = pd.DataFrame({

        "Parameter": [
            "Temperature",
            "Humidity",
            "Rain",
            "LDR",
            "Soil Moisture"
        ],

        "Value": [
            f"{temperature} °C",
            f"{humidity} %",
            f"{rain}",
            f"{ldr} %",
            f"{moisture} %"
        ]

    })


    st.table(display_data)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Tomato Crop Health Monitoring System "
    "using XGBoost Machine Learning"
)

