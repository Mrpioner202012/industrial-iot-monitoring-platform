
"""
Prueba independiente del controlador PID.

No modifica el servidor ni la base de datos.
"""

from simulator import VentilationSimulator
from pid_controller import PIDController


def main():

    simulator = VentilationSimulator()

    pid = PIDController(
        kp=15.0,
        ki=0.3,
        kd=2.0,
        setpoint=27.0
    )

    dt = 0.1
    total_time = 120.0
    control_interval = 1.0

    steps_per_control = int(
        control_interval / dt
    )

    print("=" * 66)
    print(" INDUSTRIAL IoT - PRUEBA DE CONTROL PID")
    print("=" * 66)

    print(
        f"{'Tiempo':>8} "
        f"{'Temp':>10} "
        f"{'Objetivo':>10} "
        f"{'Potencia':>12} "
        f"{'Velocidad':>12}"
    )

    print("-" * 66)

    for step in range(int(total_time / dt) + 1):

        elapsed = step * dt

        if step % steps_per_control == 0:

            state = simulator.get_state()

            power = pid.compute(
                measurement=state["temperature_c"],
                dt=control_interval
            )

            simulator.set_power(power)

            print(
                f"{elapsed:7.1f}s "
                f"{state['temperature_c']:9.2f}C "
                f"{pid.setpoint:9.2f}C "
                f"{power:11.2f}% "
                f"{state['air_speed_ms']:10.2f}m/s"
            )

        if step < int(total_time / dt):
            simulator.step(dt)

    print("-" * 66)
    print("Simulacion terminada")


if __name__ == "__main__":
    main()
