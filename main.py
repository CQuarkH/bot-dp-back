import spacy
from spacy.matcher import Matcher
import requests

# modulo de procesamiento de lenguaje natural
nlp = spacy.load("es_core_news_sm")
# identificar instrucciones de cada tipo
matcher = Matcher(nlp.vocab)

# tokens para el clima
pattern_weather = [{"LOWER": {"IN": ["clima", "tiempo", "temperatura", "pronóstico", "pronostico"]}}]

# tokens para la uf chilena
pattern_uf = [
    {"LOWER": {"IN": ["uf", "unidad", "fomento"]}},
    {"LOWER": {"IN": ["valor", "precio", "cotización", "cotizacion"]}, "OP": "?"}
]

# tokens para el dólar
pattern_dollar = [
    {"LOWER": {"IN": ["dolar", "usd", "us$"]}},
    {"LOWER": {"IN": ["valor", "precio", "cotización", "cotizacion"]}, "OP": "?"}
]

# tokens para las noticias
pattern_news = [{"LOWER": {"IN": ["noticias", "noticia", "prensa", "actualidad", "últimas", "ultimas"]}}]


matcher.add("WEATHER", [pattern_weather])
matcher.add("UF", [pattern_uf])
matcher.add("DOLAR", [pattern_dollar])
matcher.add("NEWS", [pattern_news])

# =============================================================================
# PROCESAMIENTO DE INSTRUCCIONES
# =============================================================================

def get_weather_response():
    # TODO conectar a una API de clima para obtener el pronóstico actual.
    return "El clima hoy es soleado con una temperatura de 25°C."

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
    # TODO: conectar a una API de noticias para obtener las últimas noticias.
    return "Las noticias de hoy: La economía global muestra signos de recuperación."

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
    # (aunque el viejo no mencionó nada de prioridades)
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


# interfaz de prueba para el bot
def main():
    print("Bienvenido al BOT. Escribe tu consulta (escribe 'salir' para finalizar):")
    while True:
        user_input = input(">> ")
        if user_input.strip().lower() in ["salir", "exit", "quit"]:
            print("Adiós!")
            break
        response = process_instruction(user_input)
        print(response)


if __name__ == "__main__":
    main()
