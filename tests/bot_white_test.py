import requests
from unittest.mock import patch, MagicMock
import main 
from datetime import datetime, timedelta
# -------------------------------
# White Box Tests
# -------------------------------

class FakeResponse:
    def __init__(self, json_data=None, status_code=200, raise_exc=None):
        self._json_data = json_data or {}
        self.status_code = status_code
        self._raise_exc = raise_exc

    def raise_for_status(self):
        if self._raise_exc:
            raise self._raise_exc

    def json(self):
        return self._json_data

# =====================
# Tests for process_instruction
# =====================

def test_tc18_process_instruction_no_intent():
    result = main.process_instruction("hola mundo")
    assert result == "Lo siento, no entendí la instrucción."

@patch('main.get_weather_response', return_value="weather_response")
def test_tc19_process_instruction_weather_intent(mock_weather):
    result = main.process_instruction("¿Cuál es el clima?")
    assert result == "weather_response"
    mock_weather.assert_called_once()

@patch('main.get_dollar_response', return_value="dollar_response")
@patch('main.get_uf_response', return_value="uf_response")
def test_tc20_process_instruction_multiple_intents(mock_uf, mock_dollar):
    result = main.process_instruction("Dame el valor del dolar y la UF")
    assert result in ["uf_response", "dollar_response"]

# =====================
# Tests for UF and Dollar
# =====================

def test_tc21_get_uf_response_success(monkeypatch):
    fake_data = {"uf": {"valor": 30000.5}}
    fake_resp = FakeResponse(json_data=fake_data)
    monkeypatch.setattr(requests, 'get', lambda url: fake_resp)

    resp = main.get_uf_response()
    assert "30000.50" in resp


def test_tc22_get_uf_response_failure(monkeypatch):
    def raise_error(url):
        raise requests.RequestException("fail uf")
    monkeypatch.setattr(requests, 'get', raise_error)

    resp = main.get_uf_response()
    assert "No se pudo obtener el valor de la UF" in resp


def test_tc23_get_dollar_response_success(monkeypatch):
    fake_data = {"dolar": {"valor": 800.25}}
    fake_resp = FakeResponse(json_data=fake_data)
    monkeypatch.setattr(requests, 'get', lambda url: fake_resp)

    resp = main.get_dollar_response()
    assert "800.25" in resp


def test_tc24_get_dollar_response_failure(monkeypatch):
    def raise_error(url):
        raise requests.RequestException("fail dolar")
    monkeypatch.setattr(requests, 'get', raise_error)

    resp = main.get_dollar_response()
    assert "No se pudo obtener el valor del dólar" in resp

# =====================
# Tests for News
# =====================

def test_tc25_get_news_response_success(monkeypatch):
    articles = [
        {"title": "T1", "description": "D1", "url": "U1"},
        {"title": "T2", "description": "D2", "url": "U2"},
    ]
    fake_data = {"articles": articles}
    fake_resp = FakeResponse(json_data=fake_data)
    monkeypatch.setattr(requests, 'get', lambda url: fake_resp)

    resp = main.get_news_response()
    assert "Titulo: T1" in resp
    assert "URL: U2" in resp


def test_tc26_get_news_response_no_articles(monkeypatch):
    fake_data = {"articles": []}
    fake_resp = FakeResponse(json_data=fake_data)
    monkeypatch.setattr(requests, 'get', lambda url: fake_resp)

    resp = main.get_news_response()
    assert resp == "No se encontraron noticias actuales."


def test_tc27_get_news_response_failure(monkeypatch):
    def raise_error(url):
        raise requests.RequestException("news fail")
    monkeypatch.setattr(requests, 'get', raise_error)

    resp = main.get_news_response()
    assert "No se pudo obtener las noticias" in resp

# =====================
# Tests for Weather
# =====================

def test_tc28_get_weather_response_all_success(monkeypatch):
    _tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    _yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    current = {
        "main": {"temp": 20, "humidity": 50},
        "weather": [{"description": "soleado"}],
        "wind": {"speed": 5}
    }
    yesterday = {"forecast": {"forecastday": [{"day": {"avgtemp_c": 18}, "date": _yesterday_date}]}}
    tomorrow = {"forecast": {"forecastday": [{"day": {"avgtemp_c": 22}, "date": _tomorrow_date}]}}

    responses = [FakeResponse(json_data=current),
                 FakeResponse(json_data=yesterday),
                 FakeResponse(json_data=tomorrow)]
    monkeypatch.setattr(requests, 'get', lambda url: responses.pop(0))

    resp = main.get_weather_response()
    assert "Temperatura actual: 20" in resp
    assert "Temperatura promedio de ayer: 18" in resp
    assert "Temperatura pronosticada para mañana: 22" in resp


def test_tc29_get_weather_response_openweathermap_failure(monkeypatch):
    error_resp = FakeResponse(raise_exc=requests.RequestException("owm fail"))
    yesterday = {"forecast": {"forecastday": [{"day": {"avgtemp_c": 18}, "date": "2023-10-01"}]}}
    tomorrow = {"forecast": {"forecastday": [{"day": {"avgtemp_c": 22}, "date": "2023-10-01"}]}}

    responses = [error_resp,
                 FakeResponse(json_data=yesterday),
                 FakeResponse(json_data=tomorrow)]
    monkeypatch.setattr(requests, 'get', lambda url: responses.pop(0))

    resp = main.get_weather_response()
    assert "No se pudo obtener el clima actual" in resp
    assert "Temperatura promedio de ayer: 18" in resp
    assert "Temperatura pronosticada para mañana: 22" in resp


def test_tc30_get_weather_response_yesterday_failure(monkeypatch):
    current = {
        "main": {"temp": 20, "humidity": 50},
        "weather": [{"description": "nublado"}],
        "wind": {"speed": 3}
    }
    error_yest = FakeResponse(raise_exc=requests.RequestException("hist fail"))
    tomorrow = {"forecast": {"forecastday": [{"day": {"avgtemp_c": 22}, "date": "2023-10-03"}]}}

    responses = [FakeResponse(json_data=current),
                 error_yest,
                 FakeResponse(json_data=tomorrow)]
    monkeypatch.setattr(requests, 'get', lambda url: responses.pop(0))

    resp = main.get_weather_response()
    assert "Temperatura actual: 20" in resp
    assert "No se pudo obtener la temperatura de ayer" in resp
    assert "Temperatura pronosticada para mañana: 22" in resp


def test_tc31_get_weather_response_tomorrow_failure(monkeypatch):
    current = {
        "main": {"temp": 20, "humidity": 50},
        "weather": [{"description": "lluvioso"}],
        "wind": {"speed": 4}
    }
    yesterday = {"forecast": {"forecastday": [{"day": {"avgtemp_c": 17}, "date": "2023-10-01"}]}}
    error_tom = FakeResponse(raise_exc=requests.RequestException("forecast fail"))

    responses = [FakeResponse(json_data=current),
                 FakeResponse(json_data=yesterday),
                 error_tom]
    monkeypatch.setattr(requests, 'get', lambda url: responses.pop(0))

    resp = main.get_weather_response()
    assert "Temperatura actual: 20" in resp
    assert "Temperatura promedio de ayer: 17" in resp
    assert "No se pudo obtener el pronóstico para mañana" in resp
