import pytest

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

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