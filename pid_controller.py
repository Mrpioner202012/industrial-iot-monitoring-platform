
import math


class TemperaturePID:
    """
    PID para control de temperatura mediante ventilacion.

    Si la temperatura aumenta por encima del setpoint,
    el controlador incrementa la potencia.
    """

    def __init__(
        self,
        kp=12.0,
        ki=0.35,
        kd=0.0,
        setpoint=27.0
    ):
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)
        self.setpoint = float(setpoint)

        self.integral = 0.0
        self.previous_error = None

    def reset(self):
        self.integral = 0.0
        self.previous_error = None

    def update(self, temperature, dt):
        temperature = float(temperature)
        dt = float(dt)

        if not math.isfinite(temperature):
            raise ValueError("Temperatura no valida")

        if not math.isfinite(dt) or dt <= 0:
            raise ValueError("dt debe ser positivo y finito")

        error = temperature - self.setpoint

        # Accion derivativa
        if self.previous_error is None:
            derivative = 0.0
        else:
            derivative = (
                error - self.previous_error
            ) / dt

        # Integral candidata
        proposed_integral = (
            self.integral + error * dt
        )

        # Salida sin saturar
        raw = (
            self.kp * error
            + self.ki * proposed_integral
            + self.kd * derivative
        )

        # Limitar potencia entre 0 y 100%
        output = max(
            0.0,
            min(100.0, raw)
        )

        # Anti-windup
        if (
            (0 < raw < 100)
            or (raw >= 100 and error < 0)
            or (raw <= 0 and error > 0)
        ):
            self.integral = proposed_integral

        self.previous_error = error

        return round(output, 2)
