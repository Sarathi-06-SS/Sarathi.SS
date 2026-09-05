import streamlit as st
import numpy as np
import joblib

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(page_title="Quantum XGBoost Soil Predictor")

st.title("🌱 Soil Nutrient Level Prediction")
st.write("Predict Soil Condition (Low / Medium / High)")

# ===============================
# LOAD MODEL FILES
# ===============================
model = joblib.load("quantum_xgboost_model.pkl")
scaler = joblib.load("scaler.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# ===============================
# USER INPUT SECTION
# ===============================
st.subheader("Enter Sensor Values")

N = st.number_input("Nitrogen (N)", 0.0, 100.0, 10.0)
P = st.number_input("Phosphorus (P)", 0.0, 100.0, 10.0)
K = st.number_input("Potassium (K)", 0.0, 100.0, 10.0)
T = st.number_input("Temperature (°C)", 0.0, 50.0, 25.0)
H = st.number_input("Humidity (%)", 0.0, 100.0, 50.0)
Mo = st.number_input("Moisture", 0.0, 100.0, 50.0)
LDR = st.number_input("Light Intensity (LDR)", 0.0, 100.0, 40.0)

# ===============================
# PREDICTION BUTTON
# ===============================
if st.button("Predict"):

    input_data = np.array([[N, P, K, T, H, Mo, LDR]])

    # Scale
    input_scaled = scaler.transform(input_data)

    # Predict
    prediction = model.predict(input_scaled)
    prediction_proba = model.predict_proba(input_scaled)

    predicted_label = label_encoder.inverse_transform(prediction)[0]
    confidence = np.max(prediction_proba) * 100

    st.success(f"Prediction: {predicted_label}")
    st.info(f"Confidence: {confidence:.2f}%")

    # Risk Color Indicator
    if predicted_label == "Low":
        st.warning("⚠ Soil Nutrient Level is LOW. Fertilizer Required.")
    elif predicted_label == "Medium":
        st.info("✅ Soil Nutrient Level is MEDIUM. Maintain Condition.")
    else:
        st.success("🌟 Soil Nutrient Level is HIGH. Excellent Condition!")