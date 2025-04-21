import spacy
from spacy.matcher import Matcher
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

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


def get_weather_response():
    # OpenWeatherMap API (Clima actual)
    owm_api_key = "81bfff14539fcfc8f61b3322fa84d4a2"
    city = "Temuco,CL"
    url_current = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={owm_api_key}&units=metric&lang=es"

    try:
        # Obtener el clima actual desde OpenWeatherMap
        response_current = requests.get(url_current)
        response_current.raise_for_status()
        data_current = response_current.json()

        temperature = data_current["main"]["temp"]
        description = data_current["weather"][0]["description"].capitalize()
        humidity = data_current["main"]["humidity"]
        wind_speed = data_current["wind"]["speed"]

        result = (
            f"El clima en Temuco es: {description}."
            f"Temperatura actual: {temperature}°C."
            f"Humedad: {humidity}%."
            f"Viento: {wind_speed} m/s."
        )

    except requests.RequestException as e:
        result = f"No se pudo obtener el clima de Temuco. Error: {e}"

    # Obtener la temperatura de ayer y mañana desde WeatherAPI
    api_key_weatherapi = "7826ff2c76404223bd3215456251804"
    city_weatherapi = "Temuco"

    # Fecha de ayer y mañana
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_date = yesterday.strftime('%Y-%m-%d')
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_date = tomorrow.strftime('%Y-%m-%d')

    # URL para obtener datos históricos (ayer)
    url_yesterday = f"http://api.weatherapi.com/v1/history.json?key={api_key_weatherapi}&q={city_weatherapi}&dt={yesterday_date}&lang=es"

    try:
        # Consultar los datos históricos para ayer
        response_yesterday = requests.get(url_yesterday)
        response_yesterday.raise_for_status()
        data_yesterday = response_yesterday.json()

        yesterday_temp = data_yesterday["forecast"]["forecastday"][0]["day"]["avgtemp_c"]
        result += f"Temperatura de ayer: {yesterday_temp}°C."
    except requests.RequestException as e:
        result += f"No se pudo obtener los datos históricos de ayer. Error: {e}"

    # URL para obtener el pronóstico para mañana
    url_tomorrow = f"http://api.weatherapi.com/v1/forecast.json?key={api_key_weatherapi}&q={city_weatherapi}&dt={tomorrow_date}&lang=es"

    try:
        # Consultar los datos del pronóstico para mañana
        response_tomorrow = requests.get(url_tomorrow)
        response_tomorrow.raise_for_status()
        data_tomorrow = response_tomorrow.json()

        tomorrow_temp = data_tomorrow["forecast"]["forecastday"][0]["day"]["avgtemp_c"]
        result += f"Temperatura pronosticada para mañana: {tomorrow_temp}°C."
    except requests.RequestException as e:
        result += f"No se pudo obtener el pronóstico para mañana. Error: {e}"

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

    # revisar todas las coincidencias
    for match_id, start, end in matches:
        intent = nlp.vocab.strings[match_id]
        intents.add(intent)

    # si no se encuentra ninguna coincidencia, se devuelve un mensaje de error.
    if not intents:
        return "Lo siento, no entendí la instrucción."

    # en caso de múltiples intenciones, se podría implementar una lógica de prioridad.
    # aquí se selecciona arbitrariamente la primera intención encontrada.
    selected_intent = intents.pop()

    if selected_intent == "WEATHER":
        return get_weather_response()
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
