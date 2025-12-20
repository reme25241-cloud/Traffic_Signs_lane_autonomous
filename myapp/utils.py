# utils.py

import joblib
import numpy as np
import pandas as pd
import os

# Load model components
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'models')

model = joblib.load(os.path.join(MODEL_DIR, 'disease_model.pkl'))
scaler = joblib.load(os.path.join(MODEL_DIR, 'scaler.pkl'))
label_binarizer = joblib.load(os.path.join(MODEL_DIR, 'label_binarizer.pkl'))
expected_columns = joblib.load(os.path.join(MODEL_DIR, 'feature_columns.pkl'))

def predict_disease(input_data):
    try:
        print("Input received:", input_data)
        df = pd.DataFrame([input_data])
        df_encoded = pd.get_dummies(df)

        # Add missing columns
        for col in expected_columns:
            if col not in df_encoded:
                df_encoded[col] = 0

        # Ensure correct column order
        df_encoded = df_encoded[expected_columns]

        # Scale input
        scaled_input = scaler.transform(df_encoded)

        # Predict
        preds = model.predict(scaled_input)
        labels = label_binarizer.inverse_transform(preds)

        # Generate suggestions
        suggestions = []
        for disease in labels[0]:
            if disease == "Asthma":
                suggestions.append("Avoid allergens and consult a pulmonologist.")
            elif disease == "Diabetes":
                suggestions.append("Monitor blood sugar and maintain a healthy lifestyle.")
            elif disease == "Depression":
                suggestions.append("Seek counseling or therapy support.")

        return {"diseases": labels[0], "suggestions": suggestions}
    except Exception as e:
        return {"error": str(e)}

# utils.py
from django.shortcuts import render
from .models import Patient
from .forms import PatientForm

def analyze_risk(patient):
    risks = []

    # BMI Calculation
    bmi = patient.weight_kg / ((patient.height_cm / 100) ** 2)

    # --- Asthma ---
    asthma_risk = "Low"
    if patient.allergies != "None" or patient.smoking:
        asthma_risk = "Medium"
    if patient.family_history in ["Asthma", "All"]:
        asthma_risk = "High"
    asthma = {
        "disease": "Asthma",
        "risk": asthma_risk,
        "symptoms": ["Wheezing", "Shortness of breath", "Coughing", "Chest tightness"],
        "suggestions": {
            "Low": ["Maintain a healthy environment", "Stay physically active", "Avoid known irritants"],
            "Medium": ["Use air purifiers", "Limit outdoor exposure during high pollen days", "Monitor symptoms"],
            "High": ["Consult a pulmonologist", "Consider asthma medications", "Perform regular lung function tests"]
        }[asthma_risk]
    }
    risks.append(asthma)

    # --- Diabetes ---
    diabetes_risk = "Low"
    if bmi >= 25 or patient.diet_quality == "Poor" or patient.exercise_freq == "Low":
        diabetes_risk = "Medium"
    if patient.family_history in ["Diabetes", "All"] or patient.blood_pressure >= 140:
        diabetes_risk = "High"
    diabetes = {
        "disease": "Diabetes",
        "risk": diabetes_risk,
        "symptoms": ["Frequent urination", "Excessive thirst", "Fatigue", "Blurred vision", "Weight change"],
        "suggestions": {
            "Low": ["Maintain a balanced diet", "Exercise regularly", "Monitor weight"],
            "Medium": ["Limit sugar and refined carbs", "Increase physical activity", "Schedule regular checkups"],
            "High": ["Consult a diabetologist", "Undergo blood sugar testing", "Adopt strict dietary controls"]
        }[diabetes_risk]
    }
    risks.append(diabetes)

    # --- Depression ---
    depression_risk = "Low"
    if patient.diet_quality == "Poor" or patient.exercise_freq == "Low":
        depression_risk = "Medium"
    if patient.family_history in ["Depression", "All"] or patient.alcohol_use:
        depression_risk = "High"
    depression = {
        "disease": "Depression",
        "risk": depression_risk,
        "symptoms": ["Sadness", "Loss of interest", "Fatigue", "Sleep/appetite changes", "Hopelessness"],
        "suggestions": {
            "Low": ["Maintain social connections", "Stay physically active", "Get adequate sleep"],
            "Medium": ["Practice mindfulness or meditation", "Limit screen time", "Talk to a counselor"],
            "High": ["Seek professional therapy", "Consider medication as prescribed", "Create a strong support system"]
        }[depression_risk]
    }
    risks.append(depression)

    return risks


