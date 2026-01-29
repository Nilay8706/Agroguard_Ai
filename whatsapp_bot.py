from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests

app = Flask(__name__)

import os
API_KEY = os.environ.get("1eaa4950362fd6764a1762c24b29e61e")

# 🧠 In-memory farmer database (multi-user)
farmers = {}

def get_ai_response(city, crop):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    data = requests.get(url).json()

    if "main" not in data:
        return "⚠️ Weather service unavailable."

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

    # 🦠 Disease risk
    if humidity >= 80 and temp >= 28:
        risk = "HIGH"
    elif humidity >= 65:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return (
        f"🌦️ Weather: {weather}\n"
        f"🌡️ Temp: {temp}°C\n"
        f"💧 Humidity: {humidity}%\n\n"
        f"🌱 Soil Moisture: {soil}\n"
        f"🦠 Disease Risk: {risk}\n\n"
        f"🤖 Advice:\n{irrig}\n"
        f"🌾 Crop: {crop}\n"
        f"📍 Location: {city}"
    )

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    from_number = request.values.get("From")   # farmer ID
    incoming_msg = request.values.get("Body", "").lower()

    resp = MessagingResponse()
    msg = resp.message()

    # Initialize farmer
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

    # 📊 Status command
    elif "status" in incoming_msg:
        city = farmers[from_number]["city"]
        crop = farmers[from_number]["crop"]

        if not city or not crop:
            msg.body(
                "⚠️ Please set details first:\n"
                "• location Mumbai\n"
                "• crop Wheat"
            )
        else:
            msg.body(get_ai_response(city, crop))

    else:
        msg.body(
            "👋 Welcome to AgroGuard AI 🌱\n\n"
            "Commands:\n"
            "• location <city>\n"
            "• crop <crop name>\n"
            "• status"
        )

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)

