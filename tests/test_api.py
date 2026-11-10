
"""
Industrial IoT Monitoring Platform
Automated API Tests - v0.7
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Permitir importar main.py desde la carpeta tests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import main


@pytest.fixture
def client():
    """
    Cliente de pruebas.

    No inicia el lifespan, por lo que no arranca
    el simulador, MQTT ni escribe en SQLite.
    """
    with main.state_lock:
        main.mode = "manual"
        main.simulator.temperature = 32.0
        main.simulator.air_speed = 0.0
        main.simulator.set_power(0)
        main.pid.setpoint = 27.0
        main.pid.kp = 12.0
        main.pid.ki = 0.35
        main.pid.kd = 0.0
        main.pid.reset()

    yield TestClient(main.app)

    with main.state_lock:
        main.mode = "manual"
        main.simulator.set_power(0)
        main.pid.reset()


# =========================================
# PRUEBA 1: DASHBOARD
# =========================================

def test_dashboard(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Industrial IoT Dashboard" in response.text


# =========================================
# PRUEBA 2: ESTADO DEL SISTEMA
# =========================================

def test_status(client):
    response = client.get("/api/status")

    assert response.status_code == 200

    data = response.json()

    assert "temperature_c" in data
    assert "air_speed_ms" in data
    assert "power_percent" in data
    assert "control_mode" in data
    assert "alarm" in data


# =========================================
# PRUEBA 3: CONTROL MANUAL
# =========================================

def test_manual_power(client):
    response = client.post(
        "/api/control",
        json={"power": 60}
    )

    assert response.status_code == 200
    assert response.json()["power_percent"] == 60


# =========================================
# PRUEBA 4: POTENCIA INVALIDA
# =========================================

def test_invalid_power(client):
    response = client.post(
        "/api/control",
        json={"power": 150}
    )

    assert response.status_code == 422


# =========================================
# PRUEBA 5: CAMBIO DE MODO
# =========================================

def test_automatic_mode(client):
    response = client.post(
        "/api/mode",
        json={"mode": "automatico"}
    )

    assert response.status_code == 200
    assert response.json()["control_mode"] == "automatico"


# =========================================
# PRUEBA 6: BLOQUEO DE CONTROL MANUAL
# =========================================

def test_manual_control_blocked_in_auto(client):
    client.post(
        "/api/mode",
        json={"mode": "automatico"}
    )

    response = client.post(
        "/api/control",
        json={"power": 80}
    )

    assert response.status_code == 409


# =========================================
# PRUEBA 7: CONFIGURACION PID
# =========================================

def test_pid_configuration(client):
    response = client.post(
        "/api/pid",
        json={
            "setpoint": 28,
            "kp": 12,
            "ki": 0.35,
            "kd": 0
        }
    )

    assert response.status_code == 200
    assert response.json()["setpoint_c"] == 28


# =========================================
# PRUEBA 8: SETPOINT INVALIDO
# =========================================

def test_invalid_setpoint(client):
    response = client.post(
        "/api/pid",
        json={
            "setpoint": 50,
            "kp": 12,
            "ki": 0.35,
            "kd": 0
        }
    )

    assert response.status_code == 422


# =========================================
# PRUEBA 9: ESTADO MQTT
# =========================================

def test_mqtt_status(client):
    response = client.get("/api/mqtt")

    assert response.status_code == 200

    data = response.json()

    assert data["port"] == 1883
    assert "connected" in data
    assert "telemetry_topic" in data


# =========================================
# PRUEBA 10: INFORMACION DE PLATAFORMA
# =========================================

def test_platform_info(client):
    response = client.get("/api/info")

    assert response.status_code == 200
    assert response.json()["version"] == "0.7.0"
