from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

app = Flask(__name__)

# 🌦 OpenWeather API Key (set this in Render Environment)
API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# 🧠 In-memory farmer database (multi-user)
farmers = {}


def get_ai_response(city, crop):
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={API_KEY}&units=metric"
        )
        r = requests.get(url, timeout=5)
        data = r.json()
    except Exception:
        return "⚠️ Weather service not responding. Please try again later."

    if not API_KEY:
        return "⚠️ Weather API key not configured."

    if "main" not in data:
        return "⚠️ Invalid city name or weather data unavailable."

    temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    weather = data["weather"][0]["description"]

    # 🌱 Soil + Irrigation logic
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

    # 🦠 Disease risk logic
    if humidity >= 80 and temp >= 28:
        risk = "HIGH"
    elif humidity >= 65:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return (
        f"🌦 Weather: {weather}\n"
        f"🌡 Temp: {temp}°C\n"
        f"💧 Humidity: {humidity}%\n\n"
        f"🌱 Soil Moisture: {soil}\n"
        f"🦠 Disease Risk: {risk}\n\n"
        f"🤖 Advice:\n{irrig}\n"
        f"🌾 Crop: {crop}\n"
        f"📍 Location: {city}"
    )


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    from_number = request.values.get("From")
    incoming_msg = request.values.get("Body", "").lower().strip()

    print("📩 From:", from_number)
    print("💬 Message:", incoming_msg)

    resp = MessagingResponse()

    # Initialize farmer
    if from_number not in farmers:
        farmers[from_number] = {"city": None, "crop": None}

    # 📍 Set location
    if incoming_msg.startswith("location"):
        city = incoming_msg.replace("location", "").strip().title()
        farmers[from_number]["city"] = city
        resp.message(f"✅ Location set to {city}")

    # 🌾 Set crop
    elif incoming_msg.startswith("crop"):
        crop = incoming_msg.replace("crop", "").strip().title()
        farmers[from_number]["crop"] = crop
        resp.message(f"✅ Crop set to {crop}")

    # 📊 Status command
    elif incoming_msg == "status":
        city = farmers[from_number]["city"]
        crop = farmers[from_number]["crop"]

        if not city or not crop:
            resp.message(
                "⚠️ Please set details first:\n"
                "• location Mumbai\n"
                "• crop Wheat"
            )
        else:
            resp.message(get_ai_response(city, crop))

    # ℹ️ Help / default
    else:
        resp.message(
            "👋 Welcome to AgroGuard AI 🌱\n\n"
            "Commands:\n"
            "• location <city>\n"
            "• crop <crop name>\n"
            "• status"
        )

    return str(resp)
