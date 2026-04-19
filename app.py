from flask import Flask, request, render_template
from PIL import Image
import numpy as np
from tensorflow.keras.models import load_model
import os
import pickle
from pathlib import Path

app = Flask(__name__)

# Setup paths (same as predict_disease_demo.py)
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "demo_cnn_model.h5"
REGRESSION_MODEL_PATH = BASE_DIR / "models" / "demo_regression_model.h5"
LABEL_ENCODER_PATH = BASE_DIR / "models" / "demo_label_encoder.pkl"
SCALER_PATH = BASE_DIR / "models" / "demo_scaler.pkl"

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Please ensure the file exists.")

if not REGRESSION_MODEL_PATH.exists():
    raise FileNotFoundError(f"Regression model file not found at {REGRESSION_MODEL_PATH}. Please ensure the file exists.")

if not LABEL_ENCODER_PATH.exists():
    raise FileNotFoundError(f"Label encoder file not found at {LABEL_ENCODER_PATH}. Please ensure the file exists.")

if not SCALER_PATH.exists():
    raise FileNotFoundError(f"Scaler file not found at {SCALER_PATH}. Please ensure the file exists.")

# Load models
model = load_model(MODEL_PATH)
reg_model = load_model(REGRESSION_MODEL_PATH)

# Load label encoder (same as predict_disease_demo.py)
with open(LABEL_ENCODER_PATH, 'rb') as f:
    label_encoder = pickle.load(f)

# Load scaler (same as predict_disease_demo.py)
with open(SCALER_PATH, 'rb') as f:
    scaler = pickle.load(f)

print(f"✅ Classification model loaded from: {MODEL_PATH}")
print(f"✅ Regression model loaded from: {REGRESSION_MODEL_PATH}")
print(f"✅ Label encoder loaded from: {LABEL_ENCODER_PATH}")
print(f"✅ Scaler loaded from: {SCALER_PATH}")
print(f"📊 Number of classes: {len(label_encoder)}") 

# Updated preprocessing function to match predict_disease_demo.py (MobileNetV2 with 224x224 and [0,1] normalization)
def preprocess_image(image):
    image = image.resize((224, 224))
    image_array = np.array(image)
    image_array = image_array.astype('float32') / 255.0  # Normalize to [0,1]
    return np.expand_dims(image_array, axis=0)


def decode_class_name(label_encoder, index):
    """Decode class index to class name for both dict and sequence label encoders."""
    if isinstance(label_encoder, dict):
        if index in label_encoder:
            return label_encoder[index]
        if str(index) in label_encoder:
            return label_encoder[str(index)]
        for key, value in label_encoder.items():
            if value == index:
                return key
    try:
        return label_encoder[index]
    except Exception:
        return str(index)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part", 400

        file = request.files["file"]
        if file.filename == "":
            return "No file selected", 400

        try:
            image = Image.open(file.stream).convert("RGB")
            processed_image = preprocess_image(image)
            
            # Classification prediction
            clf_prediction = model.predict(processed_image, verbose=0)

            # Regression prediction (severity)
            reg_prediction = reg_model.predict(processed_image, verbose=0)[0][0]
            print(f"🔍 Debug - Raw regression output: {reg_prediction}")
            
            severity_scaled = scaler.inverse_transform([[reg_prediction]])[0][0]
            print(f"🔍 Debug - After inverse_transform: {severity_scaled}")
            
            severity_score = float(np.clip(severity_scaled, 1.0, 10.0))
            print(f"🔍 Debug - Final severity score: {severity_score}")

            # Extract top predictions using label encoder (same as predict_disease_demo.py)
            top_indices = np.argsort(clf_prediction[0])[-3:][::-1]
            top_confidences = clf_prediction[0][top_indices]

            # Use label encoder to get class names (same as predict_disease_demo.py)
            top_predictions = [
                {"class": decode_class_name(label_encoder, int(idx)), "confidence": float(conf)}
                for idx, conf in zip(top_indices, top_confidences)
            ]

            # Map severity score to text description
            if severity_score < 4.0:
                severity_text = "Low (Nhẹ)"
            elif severity_score < 7.0:
                severity_text = "Medium (Trung bình)"
            else:
                severity_text = "High (Nặng)"

            return render_template(
                "index.html",
                result={
                    'predictions': top_predictions,
                    'severity_score': severity_score,
                    'severity_text': severity_text,
                    'main_prediction': top_predictions[0],
                },
                has_result=True
            )
        except Exception as e:
            return f"Error processing image: {e}", 500

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)