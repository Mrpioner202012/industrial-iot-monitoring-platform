
from dataclasses import dataclass
import math
import time


@dataclass
class VentilationSimulator:
    temperature: float = 32.0
    air_speed: float = 0.0
    power: float = 0.0

    ambient_temperature: float = 25.0
    max_air_speed: float = 8.0

    def step(self, dt: float = 0.1):
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError("dt debe ser positivo y finito")

        target_speed = (
            self.power / 100.0
        ) * self.max_air_speed

        # Dinamica del ventilador
        tau_motor = 2.0

        alpha = 1 - math.exp(-dt / tau_motor)

        self.air_speed += (
            target_speed - self.air_speed
        ) * alpha

        # Modelo termico simplificado
        heat_input = 0.12

        cooling = (
            0.015 + 0.018 * self.air_speed
        ) * (
            self.temperature - self.ambient_temperature
        )

        self.temperature += (
            heat_input - cooling
        ) * dt

    def set_power(self, value: float):
        value = float(value)

        if not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError(
                "La potencia debe estar entre 0 y 100"
            )

        self.power = value

    def get_state(self):
        return {
            "timestamp": time.time(),
            "temperature_c": round(
                self.temperature, 2
            ),
            "air_speed_ms": round(
                self.air_speed, 2
            ),
            "power_percent": round(
                self.power, 2
            )
        }
