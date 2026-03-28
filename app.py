"""
Wildfire Detection System with Google Gemini + Google Maps
"""

import os
import json
import base64
import io
import random
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from PIL import Image
from dotenv import load_dotenv
import google. generativeai as genai

# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)
CORS(app)

# API Keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

# Configure Gemini
model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini AI:  Configured")
    except Exception as e:
        print(f"❌ Gemini AI Error: {e}")
else:
    print("⚠️ Gemini API Key not found")

print(f"🗺️ Google Maps:  {'Configured' if GOOGLE_MAPS_API_KEY else 'Not configured'}")

# Data file
ALERTS_FILE = "data/alerts.json"

# AI Prompt for fire detection
FIRE_DETECTION_PROMPT = """
Analyze this image for fire and smoke detection. 

Respond with ONLY this JSON format (no other text):
{
    "fire_detected":  true or false,
    "smoke_detected": true or false,
    "confidence_fire": 0 to 100,
    "confidence_smoke": 0 to 100,
    "description": "What you see in the image",
    "risk_level": "none" or "low" or "medium" or "high" or "critical",
    "recommended_action": "What should be done"
}

Rules:
- Be accurate, avoid false positives
- Sunset, lights, reflections are NOT fire
- Only report fire/smoke if confident
"""


def load_alerts():
    """Load alerts from file."""
    try: 
        if os.path.exists(ALERTS_FILE):
            with open(ALERTS_FILE, 'r') as f:
                return json.load(f)
    except: 
        pass
    return []


def save_alert(alert):
    """Save alert to file."""
    alerts = load_alerts()
    alerts.insert(0, alert)
    alerts = alerts[:100]  # Keep last 100
    os.makedirs("data", exist_ok=True)
    with open(ALERTS_FILE, 'w') as f:
        json.dump(alerts, f, indent=2)


def parse_response(text):
    """Parse JSON from Gemini response."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text. strip())


# Routes
@app.route("/")
def dashboard():
    """Main dashboard with map."""
    return render_template("dashboard.html", maps_api_key=GOOGLE_MAPS_API_KEY or "")


@app.route("/api")
def api_info():
    """API information."""
    return jsonify({
        "status": "online",
        "name": "Wildfire Detection System",
        "version": "1.0",
        "gemini":  "configured" if GEMINI_API_KEY else "not configured",
        "maps":  "configured" if GOOGLE_MAPS_API_KEY else "not configured"
    })


@app.route("/api/alerts")
def get_alerts():
    """Get all alerts."""
    alerts = load_alerts()
    return jsonify({"count": len(alerts), "alerts": alerts})


@app.route("/api/statistics")
def get_statistics():
    """Get statistics."""
    alerts = load_alerts()
    return jsonify({
        "total_alerts":  len(alerts),
        "fire_alerts": sum(1 for a in alerts if a. get("fire_detected")),
        "smoke_alerts": sum(1 for a in alerts if a.get("smoke_detected")),
        "critical_alerts": sum(1 for a in alerts if a.get("risk_level") == "critical"),
        "active_devices": len(set(a.get("device_id", "unknown") for a in alerts)),
        "last_updated": datetime.now().isoformat()
    })


@app.route("/detect", methods=["POST"])
def detect():
    """Fire detection endpoint."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    if "image_base64" not in data:
        return jsonify({"error":  "No image provided"}), 400

    device_id = data. get("device_id", "unknown")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    location_name = data. get("location_name", "Unknown Location")

    # Decode image
    try:
        img_bytes = base64.b64decode(data["image_base64"])
        image = Image.open(io.BytesIO(img_bytes))
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
    except Exception as e:
        return jsonify({"error": f"Invalid image: {e}"}), 400

    # Analyze with Gemini
    if model: 
        try: 
            response = model. generate_content([FIRE_DETECTION_PROMPT, image])
            result = parse_response(response.text)
        except Exception as e: 
            return jsonify({"error": f"AI error: {e}"}), 500
    else:
        result = {
            "fire_detected": False,
            "smoke_detected": False,
            "confidence_fire":  0,
            "confidence_smoke":  0,
            "description": "Gemini AI not configured",
            "risk_level": "none",
            "recommended_action": "Configure Gemini API key"
        }

    # Create alert
    alert_data = {
        "id": f"{device_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "device_id": device_id,
        "latitude": latitude,
        "longitude": longitude,
        "location_name": location_name,
        "fire_detected": result. get("fire_detected", False),
        "smoke_detected":  result.get("smoke_detected", False),
        "alert":  result. get("fire_detected", False) or result.get("smoke_detected", False),
        "confidence_fire": result.get("confidence_fire", 0),
        "confidence_smoke":  result.get("confidence_smoke", 0),
        "risk_level": result. get("risk_level", "none"),
        "description": result.get("description", ""),
        "recommended_action": result.get("recommended_action", "")
    }

    # Save if alert detected
    if alert_data["alert"]:
        save_alert(alert_data)

    return jsonify(alert_data)


@app.route("/api/test-alert", methods=["POST"])
def test_alert():
    """Create test alert for demo."""
    data = request.get_json() or {}

    alert = {
        "id": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime. now().isoformat(),
        "device_id": "TEST-DEVICE",
        "latitude": data.get("latitude", 20 + random.random() * 10),
        "longitude": data.get("longitude", 75 + random.random() * 10),
        "location_name": f"Test Zone {random.randint(1, 100)}",
        "fire_detected": True,
        "smoke_detected": random.choice([True, False]),
        "alert": True,
        "confidence_fire":  random.randint(70, 95),
        "confidence_smoke": random. randint(50, 80),
        "risk_level": data.get("risk_level", random.choice(["medium", "high", "critical"])),
        "description": "Test fire alert for demonstration",
        "recommended_action": "This is a test - no action required"
    }

    save_alert(alert)
    return jsonify({"message": "Test alert created", "alert": alert})


@app.route("/api/clear-alerts", methods=["POST"])
def clear_alerts():
    """Clear all alerts."""
    with open(ALERTS_FILE, 'w') as f:
        json.dump([], f)
    return jsonify({"message": "All alerts cleared"})


# Main
if __name__ == "__main__": 
    print("\n" + "=" * 50)
    print("🔥 WILDFIRE DETECTION SYSTEM")
    print("=" * 50)
    print("🚀 Starting server...")
    print("📍 Dashboard: http://localhost:5000")
    print("📡 API: http://localhost:5000/api")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)