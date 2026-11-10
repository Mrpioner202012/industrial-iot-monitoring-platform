
"""
Alarmas industriales de temperatura.
Umbrales demostrativos para simulacion.
"""


def evaluate_temperature(temperature):
    temperature = float(temperature)

    if temperature >= 35:
        return {
            "level": "CRITICA",
            "message": "Temperatura crítica",
            "active": True
        }

    if temperature >= 30:
        return {
            "level": "ADVERTENCIA",
            "message": "Temperatura elevada",
            "active": True
        }

    return {
        "level": "NORMAL",
        "message": "Temperatura normal",
        "active": False
    }
