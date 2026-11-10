
"""
Industrial IoT Monitoring Platform
MQTT Monitor v0.7
"""

import json
import paho.mqtt.client as mqtt


def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties,
):
    if reason_code != 0:
        print(f"Error MQTT: {reason_code}")
        return

    print("====================================")
    print(" INDUSTRIAL IoT - MQTT MONITOR")
    print("====================================")
    print("Conectado al broker MQTT")
    print("Esperando datos industriales...\n")

    client.subscribe(
        "industrial/ventilation/telemetry"
    )

    client.subscribe(
        "industrial/ventilation/status"
    )


def on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode("utf-8")

    if topic.endswith("/status"):
        print(f"Estado del dispositivo: {payload}")
        return

    try:
        data = json.loads(payload)

        print("------------------------------------")
        print(
            f"Temperatura: {data['temperature_c']} C"
        )
        print(
            f"Velocidad:   {data['air_speed_ms']} m/s"
        )
        print(
            f"Potencia:    {data['power_percent']} %"
        )
        print(
            f"Modo:        {data['control_mode']}"
        )
        print(
            f"Setpoint:    {data['setpoint_c']} C"
        )
        print(
            f"Error PID:   {data['pid_error_c']} C"
        )

        alarm = data.get("alarm", {})
        print(
            f"Alarma:      {alarm.get('level', '--')}"
        )

    except (ValueError, KeyError) as error:
        print(f"Mensaje invalido: {error}")


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="industrial-iot-monitor",
)

client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(
        "127.0.0.1",
        1883,
        60,
    )

    client.loop_forever()

except KeyboardInterrupt:
    print("\nMonitor MQTT detenido")

finally:
    client.disconnect()
