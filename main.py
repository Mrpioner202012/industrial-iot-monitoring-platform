
"""
Industrial IoT Monitoring Platform
Version 0.7.0

FastAPI + PID + SQLite + MQTT
"""

from contextlib import asynccontextmanager
from pathlib import Path
import threading
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from simulator import VentilationSimulator
from pid_controller import TemperaturePID
from alarms import evaluate_temperature

from database import (
    initialize_database,
    save_measurement,
    save_alarm_event,
    get_measurements,
    get_alarm_events,
    get_statistics,
    export_measurements_csv,
)

from mqtt_service import MQTTService


BASE_DIR = Path(__file__).resolve().parent

simulator = VentilationSimulator()
pid = TemperaturePID()

state_lock = threading.RLock()
stop_event = threading.Event()

worker_thread = None
mode = "manual"


# =====================================
# ESTADO GENERAL
# =====================================

def current_state():
    with state_lock:
        state = simulator.get_state()

        state["alarm"] = evaluate_temperature(
            state["temperature_c"]
        )

        state["control_mode"] = mode
        state["setpoint_c"] = pid.setpoint

        state["pid_error_c"] = round(
            state["temperature_c"] - pid.setpoint,
            2,
        )

        return state


# =====================================
# CONTROL COMPARTIDO HTTP / MQTT
# =====================================

def change_power(value):
    with state_lock:
        if mode != "manual":
            raise ValueError(
                "Cambia a modo manual para fijar la potencia"
            )

        simulator.set_power(value)


def change_mode(value):
    global mode

    if value not in ("manual", "automatico"):
        raise ValueError("Modo invalido")

    with state_lock:
        if value != mode:
            pid.reset()
            mode = value


def change_setpoint(value):
    value = float(value)

    if not 25 <= value <= 40:
        raise ValueError(
            "Setpoint permitido: 25 a 40 C"
        )

    with state_lock:
        pid.setpoint = value
        pid.reset()


# =====================================
# SERVICIO MQTT
# =====================================

mqtt_service = MQTTService(
    get_state=current_state,
    set_power=change_power,
    set_mode=change_mode,
    set_setpoint=change_setpoint,
)


# =====================================
# SIMULACION INDUSTRIAL
# =====================================

def simulation_loop():
    previous_alarm = None

    last = time.monotonic()
    next_record = last

    while not stop_event.is_set():
        now = time.monotonic()

        dt = min(
            max(now - last, 0.001),
            0.5,
        )

        last = now

        with state_lock:
            if mode == "automatico":
                power = pid.update(
                    simulator.temperature,
                    dt,
                )

                simulator.set_power(power)

            simulator.step(dt)

            state = simulator.get_state()

            alarm = evaluate_temperature(
                state["temperature_c"]
            )

        if now >= next_record:
            try:
                save_measurement(state)

                alarm_key = (
                    alarm["level"],
                    alarm["message"],
                    alarm["active"],
                )

                if alarm_key != previous_alarm:
                    save_alarm_event(
                        state["timestamp"],
                        alarm,
                    )

                    previous_alarm = alarm_key

            except Exception as error:
                print(f"Error de registro: {error}")

            next_record = now + 2.0

        stop_event.wait(0.1)


# =====================================
# CICLO DE VIDA FASTAPI
# =====================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_thread

    initialize_database()

    stop_event.clear()

    worker_thread = threading.Thread(
        target=simulation_loop,
        daemon=True,
    )

    worker_thread.start()

    mqtt_service.start()

    print("Industrial IoT v0.7.0 iniciado")

    try:
        yield

    finally:
        mqtt_service.stop()

        stop_event.set()

        if worker_thread is not None:
            worker_thread.join(timeout=5)

        print("Industrial IoT detenido")


# =====================================
# APLICACION FASTAPI
# =====================================

app = FastAPI(
    title="Industrial IoT Monitoring API",
    version="0.7.0",
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


# =====================================
# MODELOS DE VALIDACION
# =====================================

class PowerCommand(BaseModel):
    power: float = Field(ge=0, le=100)


class ModeCommand(BaseModel):
    mode: str


class PIDCommand(BaseModel):
    setpoint: float = Field(ge=25, le=40)
    kp: float = Field(default=12.0, ge=0, le=100)
    ki: float = Field(default=0.35, ge=0, le=20)
    kd: float = Field(default=0.0, ge=0, le=100)


# =====================================
# DASHBOARD
# =====================================

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return (
        BASE_DIR / "templates" / "index.html"
    ).read_text(encoding="utf-8")


# =====================================
# MONITOREO
# =====================================

@app.get("/api/status")
def get_status():
    return current_state()


# =====================================
# CONTROL MANUAL
# =====================================

@app.post("/api/control")
def set_control(command: PowerCommand):
    try:
        change_power(command.power)

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    return {
        "message": "Potencia actualizada",
        **current_state(),
    }


# =====================================
# CONTROL DE MODO
# =====================================

@app.post("/api/mode")
def set_mode(command: ModeCommand):
    try:
        change_mode(command.mode)

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return {
        "message": "Modo actualizado",
        **current_state(),
    }


# =====================================
# CONFIGURACION PID
# =====================================

@app.post("/api/pid")
def configure_pid(command: PIDCommand):
    with state_lock:
        pid.setpoint = command.setpoint
        pid.kp = command.kp
        pid.ki = command.ki
        pid.kd = command.kd

        pid.reset()

        return {
            "message": "PID configurado",
            "setpoint_c": pid.setpoint,
            "kp": pid.kp,
            "ki": pid.ki,
            "kd": pid.kd,
        }


@app.get("/api/pid")
def get_pid():
    with state_lock:
        return {
            "mode": mode,
            "setpoint_c": pid.setpoint,
            "kp": pid.kp,
            "ki": pid.ki,
            "kd": pid.kd,
        }


# =====================================
# ALARMAS
# =====================================

@app.get("/api/alarms")
def get_alarms():
    state = current_state()

    return {
        "timestamp": state["timestamp"],
        "temperature_c": state["temperature_c"],
        "alarm": state["alarm"],
    }


# =====================================
# HISTORIAL
# =====================================

@app.get("/api/history")
def history(
    limit: int = Query(default=100, ge=1, le=1000)
):
    return {
        "measurements": get_measurements(limit)
    }


@app.get("/api/alarm-history")
def alarm_history(
    limit: int = Query(default=100, ge=1, le=1000)
):
    return {
        "events": get_alarm_events(limit)
    }


# =====================================
# ESTADISTICAS
# =====================================

@app.get("/api/statistics")
def statistics():
    return get_statistics()


# =====================================
# EXPORTACION CSV
# =====================================

@app.get("/api/export/csv")
def export_csv():
    return Response(
        content=export_measurements_csv(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                'attachment; filename="iot_measurements.csv"'
        },
    )


# =====================================
# ESTADO MQTT
# =====================================

@app.get("/api/mqtt")
def mqtt_status():
    return {
        "enabled": mqtt_service.running,
        "connected": mqtt_service.connected,
        "broker": mqtt_service.host,
        "port": mqtt_service.port,
        "telemetry_topic":
            "industrial/ventilation/telemetry",
        "status_topic":
            "industrial/ventilation/status",
    }


# =====================================
# INFORMACION DE PLATAFORMA
# =====================================

@app.get("/api/info")
def info():
    return {
        "name": "Industrial IoT Monitoring Platform",
        "version": "0.7.0",
        "mode": "SIMULATION",
        "database": "SQLite",
        "communication": "MQTT",
        "features": [
            "Monitoring",
            "Manual control",
            "Automatic PID",
            "Alarms",
            "SQLite history",
            "Statistics",
            "CSV export",
            "MQTT telemetry",
            "MQTT remote commands",
        ],
    }
