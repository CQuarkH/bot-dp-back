import pytest
import sys
import os

# -------------------------------
# Black Box Tests
# -------------------------------

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, process_instruction  

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_tc01_clima(client):
    response = client.post("/consulta", json={"consulta": "¿Cómo está el clima en Temuco?"})
    assert response.status_code == 200
    assert "Temperatura" in response.json["respuesta"]

def test_tc03_uf(client):
    response = client.post("/consulta", json={"consulta": "¿Cuál es el valor de la UF?"})
    assert response.status_code == 200
    assert "UF" in response.json["respuesta"]

def test_tc04_uf(client):
    response = client.post("/consulta", json={"consulta": "¿Cuál es el valor de la uf?"})
    assert response.status_code == 200
    assert "UF" in response.json["respuesta"]

def test_tc05_dolar(client):
    response = client.post("/consulta", json={"consulta": "¿Cuánto vale el dólar?"})
    assert response.status_code == 200
    assert "dólar" in response.json["respuesta"].lower()
    
def test_tc06_dolar(client):
    response = client.post("/consulta", json={"consulta": "¿Cuánto vale el dolar?"})
    assert response.status_code == 200
    assert "dólar" in response.json["respuesta"].lower()

def test_tc07_noticias(client):
    response = client.post("/consulta", json={"consulta": "Dame las noticias del día"})
    assert response.status_code == 200
    assert "Titulo" in response.json["respuesta"]
    assert "Descripcion" in response.json["respuesta"]
    assert "URL" in response.json["respuesta"]
    assert len(response.json["respuesta"]) > 0

def test_tc08_lenguaje_natural(client):
    response = client.post("/consulta", json={"consulta": "Qué onda con el tiempo"})
    assert "Temperatura" in response.json["respuesta"]

def test_tc09_lenguaje_irrelevante(client):
    response = client.post("/consulta", json={"consulta": "Me gusta el helado"})
    assert "no entendí" in response.json["respuesta"].lower()

def test_tc10_sin_consulta(client):
    response = client.post("/consulta", json={})
    assert response.status_code == 400
    assert "error" in response.json

def test_tc11_consulta_vacia(client):
        response = client.post("/consulta", json={"consulta": ""})
        assert response.status_code == 400
        assert "error" in response.json
        assert "error" in response.json


def test_method_not_allowed_on_consulta_get(client):
    response = client.get("/consulta")
    assert response.status_code == 405


def test_non_json_body(client):
    response = client.post("/consulta", data="no json body", content_type="text/plain")
    assert response.status_code == 415
    assert "error" in response.get_json()


def test_weather_synonym_pronostico(client):
    response = client.post("/consulta", json={"consulta": "¿Me das el pronóstico?"})
    assert response.status_code == 200
    text = response.json["respuesta"]
    assert ("Temperatura" in text) or text.startswith("No se pudo obtener el clima")


def test_dollar_synonym_usd(client):
    response = client.post("/consulta", json={"consulta": "Consulta USD valor"})
    assert response.status_code == 200
    assert "dólar" in response.json["respuesta"].lower()


def test_news_synonym_titulares(client):
    response = client.post("/consulta", json={"consulta": "Quiero los titulares"})
    assert response.status_code == 200
    text = response.json["respuesta"]
    assert ("Titulo" in text) or text.startswith("No se encontraron noticias")


def test_fallback_unknown_intent(client):
    response = client.post("/consulta", json={"consulta": "xyzabc"})
    assert response.status_code == 200
    assert response.json["respuesta"] == "Lo siento, no entendí la instrucción."
