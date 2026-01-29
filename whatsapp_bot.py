from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import joblib

app = Flask(__name__)

# 🌍 API KEY (Cloud-safe)
API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# 🤖 Load ML Model (already trained locally)
model = joblib.load("disease_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# 🧠 In-memory farmer database (multi-user)
farmers = {}

# 🦠 ML prediction function
def ml_disease_risk(temp, humidity, rain):
    prediction = model.predict([[temp, humidity, rain]])
    return label_encoder.inverse_transform(prediction)[0]

def get_ai_response(city, crop):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    if response.status_code != 200 or "main" not in data:
        return "⚠️ Weather service unavailable. Please try again."

    temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    weather = data["weather"][0]["description"]

    # 🌧 Rain feature for ML
    rain = 1 if "rain" in weather.lower() else 0

    # 🦠 ML-based disease risk
    risk = ml_disease_risk(temp, humidity, rain)

    # 🌱 Soil & irrigation logic (rule-based)
    if "rain" in weather.lower():
        soil = "High"
        irrig = "No irrigation needed"
    elif temp >= 32:
        soil = "Low"
        irrig = "Irrigate for 40 minutes"
    elif temp >= 28:
        soil = "Medium"
        irrig = "Irrigate for 25 minutes"
    else:
        soil = "Normal"
        irrig = "No irrigation needed"

    return (
        f"🌦️ Weather: {weather}\n"
        f"🌡️ Temp: {temp}°C\n"
        f"💧 Humidity: {humidity}%\n\n"
        f"🌱 Soil Moisture: {soil}\n"
        f"🦠 Disease Risk (ML): {risk}\n\n"
        f"🤖 Advice:\n{irrig}\n"
        f"🌾 Crop: {crop}\n"
        f"📍 Location: {city}"
    )

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    from_number = request.values.get("From")
    incoming_msg = request.values.get("Body", "").lower()

    resp = MessagingResponse()
    msg = resp.message()

    # Initialize new farmer
    if from_number not in farmers:
        farmers[from_number] = {"city": None, "crop": None}

    # 📍 Set location
    if incoming_msg.startswith("location"):
        city = incoming_msg.replace("location", "").strip().title()
        farmers[from_number]["city"] = city
        msg.body(f"✅ Location set to {city}")

    # 🌾 Set crop
    elif incoming_msg.startswith("crop"):
        crop = incoming_msg.replace("crop", "").strip().title()
        farmers[from_number]["crop"] = crop
        msg.body(f"✅ Crop set to {crop}")

    # 📊 Status
    elif "status" in incoming_msg:
        city = farmers[from_number]["city"]
        crop = farmers[from_number]["crop"]

        if not city or not crop:
            msg.body(
                "⚠️ Please set details first:\n"
                "• location Ahmedabad\n"
                "• crop Wheat"
            )
        else:
            msg.body(get_ai_response(city, crop))

    else:
        msg.body(
            "👋 Welcome to AgroGuard AI 🌱\n\n"
            "Commands:\n"
            "• location <city>\n"
            "• crop <crop>\n"
            "• status"
        )

    return str(resp)

@app.route("/")
def home():
    return "AgroGuard AI with ML is running"

if __name__ == "__main__":
    app.run()
