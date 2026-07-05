# =============================================================================
#   AI DELIVERY TIME PREDICTION — WEB APP (Flask)
#   Wraps the existing scikit-learn pipeline (models/*.pkl) behind a REST API
#   and a responsive web UI so the project can be deployed to any host
#   (Render, Railway, PythonAnywhere, Fly.io, a VPS, etc.) instead of only
#   running as a local Tkinter desktop app.
#
#   Run locally :  python app_web.py
#   Deploy      :  gunicorn app_web:app   (see Procfile / README_DEPLOYMENT.md)
# =============================================================================

import os
import io
import csv
import warnings
from datetime import datetime

import joblib
import pandas as pd
from flask import Flask, request, jsonify, render_template, send_file

warnings.filterwarnings("ignore")

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR  = os.path.join(BASE_DIR, "models")

app = Flask(__name__)

# -----------------------------------------------------------------------------
# Load model artifacts once at startup (fast requests afterwards)
# -----------------------------------------------------------------------------
_model         = joblib.load(os.path.join(MODEL_DIR, "best_model.pkl"))
_scaler        = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
_feature_names = joblib.load(os.path.join(MODEL_DIR, "feature_names.pkl"))
_label_encoders = joblib.load(os.path.join(MODEL_DIR, "label_encoders.pkl"))

# Dropdown choices, taken straight from the encoders the model was trained on
CHOICES = {col: list(le.classes_) for col, le in _label_encoders.items()}

MODEL_META = {
    "name": "Gradient Boosting Regressor",
    "r2": 0.892,
    "mae": 0.87,
    "training_rows": 45593,
}


def predict_delivery_time(sample: dict) -> float:
    """Encode + scale a raw order dict and return the predicted minutes."""
    row = dict(sample)
    for col, le in _label_encoders.items():
        if col in row:
            try:
                row[col] = le.transform([row[col]])[0]
            except ValueError:
                row[col] = 0  # unseen category fallback
    X = pd.DataFrame([row])[_feature_names]
    X_scaled = _scaler.transform(X)
    return float(_model.predict(X_scaled)[0])


def haversine_km(lat1, lon1, lat2, lon2):
    import math
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return R * 2 * math.atan2(a ** 0.5, (1 - a) ** 0.5)


def categorize(minutes: float):
    if minutes <= 25:
        return "Fast Delivery", "fast"
    elif minutes <= 40:
        return "Normal Delivery", "normal"
    return "Slow Delivery", "slow"


# =============================================================================
# ROUTES
# =============================================================================
@app.route("/")
def index():
    return render_template("index.html", choices=CHOICES, meta=MODEL_META)


@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        data = request.get_json(force=True)

        # Distance: accept a direct km value OR four GPS coordinates
        if "distance_km" in data and data["distance_km"] not in (None, ""):
            distance_km = float(data["distance_km"])
        else:
            distance_km = haversine_km(
                float(data["rest_lat"]), float(data["rest_lon"]),
                float(data["dest_lat"]), float(data["dest_lon"]),
            )

        sample = {
            "Delivery_person_Age":     float(data["age"]),
            "Delivery_person_Ratings": float(data["ratings"]),
            "Weatherconditions":       data["weather"],
            "Road_traffic_density":    data["traffic"],
            "Vehicle_condition":       int(data["vehicle_condition"]),
            "Type_of_order":           data["order_type"],
            "Type_of_vehicle":         data["vehicle_type"],
            "multiple_deliveries":     int(data["multiple_deliveries"]),
            "Festival":                data["festival"],
            "City":                    data["city"],
            "distance_km":             round(distance_km, 3),
        }

        minutes = predict_delivery_time(sample)
        label, css_class = categorize(minutes)

        return jsonify({
            "ok": True,
            "minutes": round(minutes, 1),
            "label": label,
            "css_class": css_class,
            "distance_km": round(distance_km, 2),
            "input": sample,
            "model": MODEL_META,
            "generated_at": datetime.now().strftime("%d %b %Y, %H:%M"),
        })

    except KeyError as e:
        return jsonify({"ok": False, "error": f"Missing field: {e}"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/report", methods=["POST"])
def api_report():
    """Return the last prediction as a downloadable CSV (lightweight,
    dependency-free alternative to the desktop app's PDF export)."""
    data = request.get_json(force=True)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Field", "Value"])
    writer.writerow(["Predicted Delivery Time (min)", data.get("minutes")])
    writer.writerow(["Category", data.get("label")])
    for k, v in data.get("input", {}).items():
        writer.writerow([k, v])
    writer.writerow(["Model", MODEL_META["name"]])
    writer.writerow(["R2 Score", MODEL_META["r2"]])
    writer.writerow(["Generated", datetime.now().strftime("%d %b %Y %H:%M:%S")])

    mem = io.BytesIO(buf.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(
        mem, mimetype="text/csv", as_attachment=True,
        download_name=f"delivery_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    )


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
