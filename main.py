import spacy
from spacy.matcher import Matcher
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import unicodedata
import json

def normalize_text(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower()

# Cargar lista de ciudades desde el archivo cities.json
with open("assets/cities.json", encoding="utf-8") as f:
    cities_data = json.load(f)
    city_mapping = {
    normalize_text(city): city for city in cities_data["ciudades"]
}

# modulo de procesamiento de lenguaje natural
nlp = spacy.load("es_core_news_sm")
# identificar instrucciones de cada tipo
matcher = Matcher(nlp.vocab)

# tokens para el clima
pattern_weather = [
    {"LOWER": {"IN": ["clima", "tiempo", "temperatura", "pronóstico", "pronostico"]}}]

# tokens para la uf chilena
pattern_uf = [
    {"LOWER": {"IN": ["uf", "unidad", "fomento"]}},
    {"LOWER": {"IN": ["valor", "precio",
                      "cotización", "cotizacion"]}, "OP": "?"}
]

# tokens para el dólar
pattern_dollar = [
    {"LOWER": {"IN": ["dolar", "dólar", "usd", "us$"]}},
    {"LOWER": {"IN": ["valor", "precio",
                      "cotización", "cotizacion"]}, "OP": "?"}
]

# tokens para las noticias
pattern_news = [{"LOWER": {"IN": ["noticias", "noticia", "prensa", "actualidad", "últimas", "ultimas", "titulares"]}}]


matcher.add("WEATHER", [pattern_weather])
matcher.add("UF", [pattern_uf])
matcher.add("DOLAR", [pattern_dollar])
matcher.add("NEWS", [pattern_news])

# =============================================================================
# PROCESAMIENTO DE INSTRUCCIONES
# =============================================================================

def get_weather_response(city_name="Temuco"):
    owm_api_key = "81bfff14539fcfc8f61b3322fa84d4a2"
    city = f"{city_name},CL"
    url_current = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={owm_api_key}&units=metric&lang=es"

    try:
        response_current = requests.get(url_current)
        response_current.raise_for_status()
        data_current = response_current.json()

        temperature = data_current["main"]["temp"]
        description = data_current["weather"][0]["description"].capitalize()
        humidity = data_current["main"]["humidity"]
        wind_speed = data_current["wind"]["speed"]

        result = (
            f"El clima actual en {city_name} es: {description}. "
            f"Temperatura: {temperature}°C. "
            f"Humedad: {humidity}%. "
            f"Viento: {wind_speed} m/s. "
        )

    except requests.RequestException as e:
        result = f"No se pudo obtener el clima actual. Error: {e}"
        return result

    # WeatherAPI - Temperatura de ayer y mañana
    api_key_weatherapi = "7826ff2c76404223bd3215456251804"
    base_url = "http://api.weatherapi.com/v1"

    # Fechas
    yesterday = datetime.now() - timedelta(days=1)
    tomorrow = datetime.now() + timedelta(days=1)

    yesterday_date = yesterday.strftime('%Y-%m-%d')
    tomorrow_date = tomorrow.strftime('%Y-%m-%d')

    # --- Ayer (historial) ---
    try:
        url_yesterday = f"{base_url}/history.json?key={api_key_weatherapi}&q={city_name}&dt={yesterday_date}&lang=es"
        response_yesterday = requests.get(url_yesterday)
        response_yesterday.raise_for_status()
        data_yesterday = response_yesterday.json()
        temp_yesterday = data_yesterday["forecast"]["forecastday"][0]["day"]["avgtemp_c"]

        result += f" Temperatura promedio de ayer: {temp_yesterday}°C."

    except requests.RequestException as e:
        result += f" No se pudo obtener la temperatura de ayer. Error: {e}"

    # --- Mañana (pronóstico) ---
    try:
        url_forecast = f"{base_url}/forecast.json?key={api_key_weatherapi}&q={city_name}&days=2&lang=es"
        response_forecast = requests.get(url_forecast)
        response_forecast.raise_for_status()
        data_forecast = response_forecast.json()

        for day in data_forecast["forecast"]["forecastday"]:
            if day["date"] == tomorrow_date:
                temp_tomorrow = day["day"]["avgtemp_c"]
                result += f" Temperatura pronosticada para mañana: {temp_tomorrow}°C."

    except requests.RequestException as e:
        result += f" No se pudo obtener el pronóstico de mañana. Error: {e}"

    return result

def get_uf_response():
    try:
        response = requests.get("https://mindicador.cl/api")
        response.raise_for_status()
        data = response.json()
        uf_value = data["uf"]["valor"]
        return f"El valor actual de la UF es ${uf_value:.2f} CLP."
    except requests.RequestException as e:
        return f"No se pudo obtener el valor de la UF. Error: {e}"


def get_dollar_response():
    try:
        response = requests.get("https://mindicador.cl/api")
        response.raise_for_status()
        data = response.json()
        dollar_value = data["dolar"]["valor"]
        return f"El valor actual del dólar es ${dollar_value:.2f} CLP."
    except requests.RequestException as e:
        return f"No se pudo obtener el valor del dólar. Error: {e}"


def get_news_response():
    api_key = "dbc3f7face4f57606d7a0046577ec01b"
    url = (
        f"https://gnews.io/api/v4/top-headlines"
        f"?lang=es"
        f"&max=5"
        f"&apikey={api_key}"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])[:5]
        if not articles:
            return "No se encontraron noticias actuales."

        news = "\n\n".join(
            f"Titulo: {a.get('title', 'Sin título')}\n"
            f"Descripcion: {a.get('description', 'Sin descripción')}\n"
            f"URL: {a.get('url', '')}"
            for a in articles
        )
        return news

    except requests.RequestException as e:
        return f"No se pudo obtener las noticias. Error: {e}"

# =============================================================================
# Función para procesar la instrucción del usuario (Capa de Lógica)
# =============================================================================


def process_instruction(text: str):
    doc = nlp(text)
    matches = matcher(doc)
    intents = set()

    # Normaliza el texto para compararlo
    normalized_text = normalize_text(text)
    detected_city = None
    for norm_city, original_city in city_mapping.items():
        if norm_city in normalized_text:
            detected_city = original_city
            break

    for match_id, start, end in matches:
        intent = nlp.vocab.strings[match_id]
        intents.add(intent)

    if not intents:
        return "Lo siento, no entendí la instrucción."

    selected_intent = intents.pop()

    if selected_intent == "WEATHER":
        return get_weather_response(detected_city if detected_city else "Temuco")
    elif selected_intent == "UF":
        return get_uf_response()
    elif selected_intent == "DOLAR":
        return get_dollar_response()
    elif selected_intent == "NEWS":
        return get_news_response()
    else:
        return "Lo siento, no puedo procesar esa instrucción."


app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas


@app.route("/")
def home():
    return jsonify({"consulta": "Bienvenido al BOT API de Clima, UF, Dólar y Noticias"})


@app.route("/consulta", methods=["POST"])
def consulta():
    data = request.get_json()
    if not data or "consulta" not in data:
        return jsonify({"error": "Falta el campo 'mensaje' en el cuerpo de la solicitud."}), 400

    if not data["consulta"]:
        return jsonify({"error": "El campo 'mensaje' no puede estar vacío."}), 400

    user_input = data["consulta"]
    respuesta = process_instruction(user_input)
    return jsonify({"respuesta": respuesta} if isinstance(respuesta, str) else respuesta)


if __name__ == "__main__":
    app.run(debug=True)
