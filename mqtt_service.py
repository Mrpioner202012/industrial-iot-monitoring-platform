
import json
import threading

import paho.mqtt.client as mqtt


class MQTTService:
    BASE_TOPIC = "industrial/ventilation"

    def __init__(
        self,
        get_state,
        set_power,
        set_mode,
        set_setpoint,
        host="127.0.0.1",
        port=1883,
    ):
        self.get_state = get_state
        self.set_power = set_power
        self.set_mode = set_mode
        self.set_setpoint = set_setpoint

        self.host = host
        self.port = port

        self.connected = False
        self.running = False

        self.stop_event = threading.Event()
        self.worker = None

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="industrial-iot-platform",
        )

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        self.client.will_set(
            f"{self.BASE_TOPIC}/status",
            payload="offline",
            qos=1,
            retain=True,
        )

    def on_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties,
    ):
        if reason_code != 0:
            self.connected = False
            print(f"MQTT: conexion rechazada: {reason_code}")
            return

        self.connected = True
        print("MQTT: conectado al broker")

        client.subscribe(
            f"{self.BASE_TOPIC}/command/+",
            qos=1,
        )

        client.publish(
            f"{self.BASE_TOPIC}/status",
            payload="online",
            qos=1,
            retain=True,
        )

    def on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags,
        reason_code,
        properties,
    ):
        self.connected = False
        print(f"MQTT: desconectado ({reason_code})")

    def on_message(self, client, userdata, message):
        try:
            topic = message.topic
            payload = message.payload.decode("utf-8").strip()

            if topic == f"{self.BASE_TOPIC}/command/power":
                value = float(payload)

                if not 0 <= value <= 100:
                    raise ValueError("Potencia fuera de rango")

                self.set_power(value)
                print(f"MQTT: potencia -> {value}%")

            elif topic == f"{self.BASE_TOPIC}/command/mode":
                if payload not in ("manual", "automatico"):
                    raise ValueError("Modo invalido")

                self.set_mode(payload)
                print(f"MQTT: modo -> {payload}")

            elif topic == f"{self.BASE_TOPIC}/command/setpoint":
                value = float(payload)

                if not 25 <= value <= 40:
                    raise ValueError("Setpoint fuera de rango")

                self.set_setpoint(value)
                print(f"MQTT: setpoint -> {value} C")

        except (ValueError, UnicodeDecodeError) as error:
            print(f"MQTT: comando rechazado: {error}")

        except Exception as error:
            print(f"MQTT: error procesando comando: {error}")

    def publish_loop(self):
        while not self.stop_event.is_set():
            if self.connected:
                try:
                    state = self.get_state()

                    payload = json.dumps(
                        state,
                        ensure_ascii=False,
                        allow_nan=False,
                    )

                    self.client.publish(
                        f"{self.BASE_TOPIC}/telemetry",
                        payload=payload,
                        qos=0,
                    )

                except Exception as error:
                    print(f"MQTT: error publicando: {error}")

            self.stop_event.wait(2)

    def start(self):
        if self.running:
            return

        self.running = True
        self.stop_event.clear()

        self.client.connect_async(
            self.host,
            self.port,
            keepalive=60,
        )

        self.client.loop_start()

        self.worker = threading.Thread(
            target=self.publish_loop,
            daemon=True,
        )

        self.worker.start()
        print("MQTT: servicio iniciado")

    def stop(self):
        if not self.running:
            return

        self.stop_event.set()

        if self.worker is not None:
            self.worker.join(timeout=5)

        if self.connected:
            self.client.publish(
                f"{self.BASE_TOPIC}/status",
                payload="offline",
                qos=1,
                retain=True,
            ).wait_for_publish(timeout=2)

        self.client.disconnect()
        self.client.loop_stop()

        self.connected = False
        self.running = False

        print("MQTT: servicio detenido")
