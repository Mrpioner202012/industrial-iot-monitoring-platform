
# Industrial IoT Monitoring Platform

A Python-based Industrial IoT monitoring and control platform
for a simulated industrial ventilation system.

## Overview

This project demonstrates industrial automation,
real-time monitoring, feedback control, and IoT communication.

The platform simulates a ventilation process and provides
a web dashboard for monitoring temperature, airflow,
fan power, and system alarms.

It supports manual control and automatic PID temperature
regulation.

## Technologies

- Python
- FastAPI
- MQTT (Eclipse Mosquitto)
- Paho MQTT
- SQLite
- Chart.js
- HTML, CSS, JavaScript
- Pytest

## Features

- Industrial ventilation simulation
- Real-time temperature and airflow monitoring
- Interactive web dashboard
- Manual fan power control
- Automatic PID temperature control
- Temperature alarm monitoring
- SQLite measurement history
- CSV data export
- MQTT telemetry publishing
- Remote MQTT commands
- REST API documentation
- Automated API tests

## Architecture

Simulated Ventilation Process
        |
        v
Python Simulation + PID
        |
        v
FastAPI Backend
        |
        +----> Web Dashboard
        |
        +----> SQLite Database
        |
        +----> MQTT Broker
                    |
                    v
              MQTT Monitor

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/industrial-iot-monitoring-platform.git
cd industrial-iot-monitoring-platform
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Install and start an Eclipse Mosquitto MQTT broker
on localhost, port 1883.

Run the application:

```bash
python -m uvicorn main:app --reload
```

Open:

http://127.0.0.1:8000

## MQTT Topics

| Topic | Description |
|---|---|
| industrial/ventilation/telemetry | Real-time measurements |
| industrial/ventilation/status | MQTT connection status |
| industrial/ventilation/command/power | Manual fan power |
| industrial/ventilation/command/mode | Manual or automatic mode |
| industrial/ventilation/command/setpoint | Temperature setpoint |

## MQTT Monitor

Run:

```bash
python mqtt_monitor.py
```

## Automated Tests

Run:

```bash
python -m pytest tests/test_api.py -v
```

The project includes automated tests covering API
responses, control modes, PID configuration,
and input validation.

## Current Limitations

- The industrial process is simulated.
- No physical PLC or sensor is connected.
- The MQTT broker runs locally.
- MQTT authentication and TLS are not configured.
- Long-term PID stability has not been formally validated.

## Future Improvements

- ESP32 sensor integration
- PLC communication
- MQTT authentication and TLS
- Historical process analysis
- PID performance evaluation

## Author

Jesús Eduardo Vega Córdova

Electronic Instrumentation Engineering Student