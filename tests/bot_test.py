import pytest

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, process_instruction  

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# -------------------------------
# Black Box Tests
# -------------------------------

def test_tc01_clima(client):
    response = client.post("/consulta", json={"consulta": "¿Cómo está el clima en Temuco?"})
    assert response.status_code == 200
    assert "Temperatura" in response.json["respuesta"]

def test_tc02_clima_api_error(monkeypatch, client):
    def mock_get(*args, **kwargs):
        raise Exception("Error simulado")
    monkeypatch.setattr("requests.get", mock_get)
    response = client.post("/consulta", json={"consulta": "¿Qué clima hace?"})
    assert "Error" in response.json["respuesta"]

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

    # -------------------------------
# White Box Tests
# -------------------------------

def test_process_instruction_clima_whitebox():
    texto = "¿Cuál es el pronóstico del clima hoy?"
    resultado = process_instruction(texto)
    assert "temperatura" in resultado.lower() or "clima" in resultado.lower()

def test_process_instruction_uf_whitebox():
    texto = "¿Cuánto vale la unidad de fomento?"
    resultado = process_instruction(texto)
    assert "uf" in resultado.lower() or "$" in resultado.lower()

def test_process_instruction_dolar_whitebox():
    texto = "¿Me puedes decir el precio del dolar?"
    resultado = process_instruction(texto)
    assert "dólar" in resultado.lower() or "$" in resultado.lower()

def test_process_instruction_news_whitebox():
    texto = "Muéstrame las últimas noticias"
    resultado = process_instruction(texto)
    assert "titulo" in resultado.lower() or "noticia" in resultado.lower()

def test_process_instruction_no_match_whitebox():
    texto = "hola"
    resultado = process_instruction(texto)
    assert resultado == "Lo siento, no entendí la instrucción."