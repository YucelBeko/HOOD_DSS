import streamlit as st
import fitz  # PyMuPDF
import re
import json
import pandas as pd
import joblib

# Model & Scaler
model = joblib.load("model_gpr.pkl")
scaler = joblib.load("scaler.pkl") 


# --- Utility Function to Extract Values ---
def extract_value(pattern, text):
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", "."))
    return None

# --- Streamlit App ---

motor_options = {
    "Robin Good T & 3 Camlı": {
        "type": "PSC",
        "part_number": "164732006",
        "levels": {
            "lvl1": {"power_W": 120, "rpm": 600},
            "lvl2": {"power_W": 160, "rpm": 950},
            "lvl3": {"power_W": 220, "rpm": 1400, "flow_m3h": 600},
        }
    },
    "Robin Good+ Eğik": {
        "type": "PSC",
        "part_number": "164732005",
        "levels": {
            "lvl1": {"power_W": 140, "rpm": 550},
            "lvl2": {"power_W": 170, "rpm": 800},
            "lvl3": {"power_W": 200, "rpm": 1000},
            "boost": {"power_W": 280, "rpm": 1600, "flow_m3h": 720}
        }
    },
    "Robin Good Eğik": {
        "type": "PSC",
        "part_number": "164732008",
        "levels": {
            "lvl1": {"power_W": 95, "rpm": 550},
            "lvl2": {"power_W": 115, "rpm": 800},
            "lvl3": {"power_W": 145, "rpm": 1000, "flow_m3h": 410}
        },
        "note": "Different cable length than 164732014"
    },
    "Robin Street Fighter": {
        "type": "Gölge Kutuplu",
        "part_number": "164721020",
        "levels": {
            "lvl1": {"power_W": 55, "rpm": 1100},
            "lvl2": {"power_W": 74, "rpm": 1600},
            "lvl3": {"power_W": 86, "rpm": 2150, "flow_m3h": 345}
        }
    },
    "Robin Better-Best Eğik": {
        "type": "BLDC",
        "part_number": "164732007",
        "levels": {
            "lvl1": {"power_W": "3-8", "rpm": 510},
            "lvl2": {"power_W": "11-18", "rpm": 850},
            "lvl3": {"power_W": "25-32", "rpm": 1070},
            "boost": {"power_W": 230, "rpm": 2050, "flow_m3h": 850}
        },
        "note": "Different cable length than 164732013"
    },
    "Robin Better-Best T": {
        "type": "BLDC",
        "part_number": "164732013",
        "levels": {
            "lvl1": {"power_W": "3-8", "rpm": 510},
            "lvl2": {"power_W": "11-18", "rpm": 850},
            "lvl3": {"power_W": "25-32", "rpm": 1070},
            "boost": {"power_W": 230, "rpm": 2050, "flow_m3h": 850}
        },
        "note": "Different cable length than 164732007"
    },
    "Robin Mekanik Fighter": {
        "type": "PSC",
        "part_number": "164732014",
        "levels": {
            "lvl1": {"power_W": 95, "rpm": 550},
            "lvl2": {"power_W": 115, "rpm": 800},
            "lvl3": {"power_W": 145, "rpm": 1000, "flow_m3h": 400}
        },
        "note": "Different cable length than 164732008, soldered wire ends"
    },
    "Hobex Motoru": {
        "type": "BLDC",
        "part_number": "164265001",
        "levels": {
            "lvl1": {"power_W": 19, "rpm": 460},
            "lvl2": {"power_W": 48, "rpm": 990},
            "lvl3": {"power_W": 130, "rpm": 1475},
            "boost": {"power_W": 160, "rpm": 1600}
        }
    },
    "Robin Good+ T": {
        "type": "PSC",
        "part_number": "164732003",
        "levels": {
            "lvl1": {"power_W": 130, "rpm": 550},
            "lvl2": {"power_W": 160, "rpm": 800},
            "lvl3": {"power_W": 190, "rpm": 1000},
            "boost": {"power_W": 270, "rpm": 1600, "flow_m3h": 710}
        }
    }
}

st.title("PDF Report Extractor")

# File uploader
uploaded_file = st.file_uploader("Upload your test report (.pdf)", type="pdf")

if uploaded_file is not None:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    # --- Extracted Data ---
    test_environment = {
        "temperature_C": extract_value(r"Test room air temperature\s*\[°C\]\s*([0-9]+[.,]?[0-9]*)", text),
        "humidity_percent": extract_value(r"Test room air humidity\s*\[%\]\s*([0-9]+[.,]?[0-9]*)", text),
        "air_pressure_hPa": extract_value(r"Ambient air pressure\s*\[hPa\]\s*([0-9]+[.,]?[0-9]*)", text)
    }

    performance_data = {
        "fde_bep_percent": extract_value(r"FDEhood_BEP\s*([0-9]+[.,]?[0-9]*)", text),
        "q_bep_m3h": extract_value(r"QBEP\s*([0-9]+[.,]?[0-9]*)", text),
        "p_bep_ref_W": extract_value(r"PBEP_Ref\s*([0-9]+[.,]?[0-9]*)\s*W", text),
        "p_light_measured_W": extract_value(r"PL\s*([0-9]+[.,]?[0-9]*)", text),
        "delta_p_bep_ref_Pa": extract_value(r"[Δ∆]?\s*pBEP_Ref\s*([0-9]+[.,]?[0-9]*)\s*Pa", text)
    }

    st.success("PDF parsed successfully.")


    # --- Manual Fields ---
    st.subheader("Additional Information")

    # Split form into two columns
    col1, col2 = st.columns(2)

    # --- Left Column ---
    with col1:
        # Platform input
        platform_option = st.selectbox("Select Platform", ["Eğik", "T"])
        platform = "egik" if platform_option == "Eğik" else "t"

        # Width input
        width = st.radio(
            "Select Width (cm)",
            options=[60, 90],
            horizontal=True
        )

        # Glass count: platform'a göre seçenekleri belirle
        if platform == "egik":
            glass_options = [1, 2, 3]
        else:
            glass_options = [0]

        glass_count = st.selectbox(
            "Glass Count",
            options=glass_options,
            format_func=lambda x: f"{x} (T tipi)" if x == 0 else str(x)
        )

    # --- Right Column ---
    with col2:
        # Segment input
        segment_option = st.selectbox("Select Segment", ["Good", "Good+"])
        segment = "good" if segment_option == "Good" else "good_p"

        # Filter Layer input
        filter_layer = st.number_input("Filter Layer", min_value=0, step=1)

        # Mode selection
        mod_option = st.selectbox("Select Mode", ["Level 1", "Level 2", "Level 3", "Boost"])
        if mod_option == "Level 1":
            mod = "lvl1"
        elif mod_option == "Level 2":
            mod = "lvl2"
        elif mod_option == "Level 3":
            mod = "lvl3"
        else:
            mod = "boost"

    # --- Motor Selection ---
    good_motors = [
        "Robin Good T & 3 Camlı",
        "Robin Good Eğik",
        "Robin Street Fighter",
        "Robin Mekanik Fighter"
    ]

    good_p_motors = [
        "Robin Good+ Eğik",
        "Robin Good+ T",
    ]

    better_best_motors = [
        "Robin Better-Best Eğik",
        "Robin Better-Best T",
        "Hobex Motoru"
    ]

    # Segment'e göre motorları filtrele
    if segment == "good":
        filtered_motor_options = {
            k: v for k, v in motor_options.items() if k in good_motors
        }
    elif segment == "good_p":
        filtered_motor_options = {
            k: v for k, v in motor_options.items() if k in good_p_motors
        }
    else:
        filtered_motor_options = motor_options  # fallback (shouldn’t happen)

    motor_name = st.selectbox("Select Motor", list(filtered_motor_options.keys()))
    motor_specs = filtered_motor_options[motor_name]
    level_specs = motor_specs["levels"][mod]


    # --- Final JSON ---
    combined_data = {
        "test_environment": test_environment,
        "performance_data": performance_data,
        "manual_fields": {
            "platform": platform,
            "segment": segment,
            "width": width,
            "glass_count": glass_count,
            "filter_layer": filter_layer,
            "mod": mod,
        },
        "motor_output": {
            "power_W": level_specs["power_W"],
            "rpm": level_specs["rpm"],
            "flow_m3h": level_specs.get("flow_m3h", None),
            "type": motor_specs["type"]
        }
    }

    st.subheader("Generated JSON")
    st.json(combined_data)

    # Download button
    json_data = json.dumps(combined_data, indent=4)
    st.download_button("Download JSON", data=json_data, file_name="report_data.json", mime="application/json")

# After form inputs and combined_data creation

st.markdown("---")
st.subheader("Run Model Prediction")

def prepare_features_from_json(combined_data, expected_columns):
    perf = combined_data.get("performance_data", {})
    env = combined_data.get("test_environment", {})
    manual = combined_data.get("manual_fields", {})
    motor = combined_data.get("motor_output", {})

    # Raw features
    base_data = {
        "Width": manual.get("width", 0),
        "Temp": env.get("temperature_C", 0),
        "Hum": env.get("humidity_percent", 0),
        "Pressure": env.get("air_pressure_hPa", 0),
        "Filter_Layer": manual.get("filter_layer", 0),
        "Motor_Power": motor.get("power_W", 0),
        "Motor_Flow": motor.get("flow_m3h", 0),
        "Motor_RPM": motor.get("rpm", 0),
        "Chimney": manual.get("chimney", 150),  # default/fallback
        "Lamp_Power": perf.get("p_light_measured_W", 0),
    }

    # One-hot encode manual fields
    one_hots = {
        f"Platform_{manual.get('platform')}": 1,
        f"Segment_{manual.get('segment')}": 1,
        f"Glass_Count_{manual.get('glass_count')} cam": 1,
        f"Motor_Type_{motor.get('type')}": 1,
        f"Mod_{manual.get('mod')}": 1,
    }

    # Combine all
    full_data = {**base_data, **one_hots}

    # Convert to DataFrame and reindex to match feature order
    df = pd.DataFrame([full_data])
    df = df.reindex(columns=expected_columns, fill_value=0)

    return df, perf.get("fde_bep_percent", None)

expected_features = joblib.load("feature_names.pkl")  # Load the expected column order

if st.button("Run Prediction"):
    try:
        input_df, actual_fde = prepare_features_from_json(combined_data, expected_features)

        # Scale
        X_scaled = scaler.transform(input_df)

        # Predict
        y_pred, y_std = model.predict(X_scaled, return_std=True)
        confidence_z = 1.96  # or 2.576 for 99%
        ci_low = y_pred[0] - confidence_z * y_std[0]
        ci_high = y_pred[0] + confidence_z * y_std[0]

        # Show results
        st.subheader("Prediction Result")
        st.write(f"Predicted FDE: **{y_pred[0]:.2f}%**")
        st.write(f"95% Confidence Interval: **[{ci_low:.2f}% - {ci_high:.2f}%]**")

        # New DSS logic
        if actual_fde is not None:
            if actual_fde < ci_low or actual_fde > ci_high:
                st.warning(
                    f"Actual FDE ({actual_fde:.2f}%) is outside the predicted confidence interval. "
                    "Repeating the test is recommended."
                )
            else:
                st.success("Actual FDE is within the model's confidence interval. No repeat needed.")
        else:
            if y_std[0] > 2.5:
                st.warning("Prediction uncertainty is high. Repeating the test is recommended.")
            else:
                st.success("Confidence is acceptable. No repeat needed.")

    except Exception as e:
        st.error(f"Prediction failed: {e}")
