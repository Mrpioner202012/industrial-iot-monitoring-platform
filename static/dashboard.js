
const el = id => document.getElementById(id);

const chartData = {
    labels: [],
    temp: [],
    speed: []
};

let tempChart = null;
let speedChart = null;
let currentMode = "manual";


function createChart(canvasId, label, color) {
    const canvas = el(canvasId);

    if (!canvas || typeof Chart === "undefined") {
        return null;
    }

    return new Chart(canvas, {
        type: "line",

        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                borderColor: color,
                backgroundColor: color,
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.25
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,

            scales: {
                x: {
                    ticks: {
                        color: "#a7bad0",
                        maxTicksLimit: 7
                    },
                    grid: {
                        color: "#34465f"
                    }
                },

                y: {
                    ticks: {
                        color: "#a7bad0"
                    },
                    grid: {
                        color: "#34465f"
                    }
                }
            },

            plugins: {
                legend: {
                    labels: {
                        color: "#f3f7ff"
                    }
                }
            }
        }
    });
}


function updateCharts(state) {
    const time = new Date(
        state.timestamp * 1000
    ).toLocaleTimeString("es-MX");

    chartData.labels.push(time);
    chartData.temp.push(state.temperature_c);
    chartData.speed.push(state.air_speed_ms);

    if (chartData.labels.length > 60) {
        chartData.labels.shift();
        chartData.temp.shift();
        chartData.speed.shift();
    }

    if (tempChart) {
        tempChart.data.labels = chartData.labels;
        tempChart.data.datasets[0].data = chartData.temp;
        tempChart.update("none");
    }

    if (speedChart) {
        speedChart.data.labels = chartData.labels;
        speedChart.data.datasets[0].data = chartData.speed;
        speedChart.update("none");
    }
}


function updateMode(mode) {
    currentMode = mode;

    el("currentMode").textContent =
        mode === "automatico"
            ? "Automático PID"
            : "Manual";

    el("manualControls").hidden =
        mode !== "manual";

    el("manualMode").classList.toggle(
        "selected",
        mode === "manual"
    );

    el("autoMode").classList.toggle(
        "selected",
        mode === "automatico"
    );
}


async function request(url, options = {}) {
    const response = await fetch(url, {
        cache: "no-store",
        ...options
    });

    if (!response.ok) {
        let detail = `HTTP ${response.status}`;

        try {
            const body = await response.json();
            detail = body.detail || detail;
        } catch (_) {}

        throw new Error(detail);
    }

    return response.json();
}


async function post(url, payload) {
    return request(url, {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(payload)
    });
}


function message(text, error = false) {
    el("feedback").textContent = text;

    el("feedback").style.color =
        error ? "#fca5a5" : "#7dd3fc";
}


async function refreshStatus() {
    try {
        const state = await request("/api/status");

        el("temperature").textContent =
            `${Number(state.temperature_c).toFixed(2)} °C`;

        el("speed").textContent =
            `${Number(state.air_speed_ms).toFixed(2)} m/s`;

        el("power").textContent =
            `${Number(state.power_percent).toFixed(1)}%`;

        el("pidError").textContent =
            `${Number(state.pid_error_c).toFixed(2)} °C`;

        if (state.control_mode !== currentMode) {
            updateMode(state.control_mode);
        }

        if (
            document.activeElement !== el("powerSlider")
        ) {
            el("powerSlider").value =
                state.power_percent;

            el("requestedPower").textContent =
                `${Math.round(state.power_percent)}%`;
        }

        // ALARMAS

        const alarm = state.alarm;

        el("alarmLevel").textContent =
            alarm.level;

        el("alarmMessage").textContent =
            alarm.message;

        let alarmClass = "normal";

        if (alarm.level === "CRITICA") {
            alarmClass = "critica";
        } else if (alarm.level === "ADVERTENCIA") {
            alarmClass = "advertencia";
        }

        el("alarmBox").className =
            `alarm ${alarmClass}`;

        // CONEXION

        el("connection").textContent =
            "● Sistema conectado";

        el("connection").style.color =
            "#86efac";

        updateCharts(state);

    } catch (err) {
        el("connection").textContent =
            `● Sin conexión: ${err.message}`;

        el("connection").style.color =
            "#fca5a5";

        console.error(err);
    }
}


async function refreshStats() {
    try {
        const stats = await request(
            "/api/statistics"
        );

        el("totalMeasurements").textContent =
            stats.total_measurements;

        el("avgTemp").textContent =
            stats.avg_temperature_c == null
                ? "--"
                : `${stats.avg_temperature_c} °C`;

        el("maxTemp").textContent =
            stats.max_temperature_c == null
                ? "--"
                : `${stats.max_temperature_c} °C`;

        el("avgSpeed").textContent =
            stats.avg_air_speed_ms == null
                ? "--"
                : `${stats.avg_air_speed_ms} m/s`;

    } catch (err) {
        console.error("Estadísticas:", err);
    }
}


async function init() {
    tempChart = createChart(
        "temperatureChart",
        "Temperatura (°C)",
        "#fb923c"
    );

    speedChart = createChart(
        "speedChart",
        "Velocidad (m/s)",
        "#38bdf8"
    );

    if (!tempChart || !speedChart) {
        message(
            "No se pudo cargar Chart.js. Comprueba internet.",
            true
        );
    }

    // CONTROL MANUAL

    el("powerSlider").addEventListener(
        "input",
        () => {
            el("requestedPower").textContent =
                `${el("powerSlider").value}%`;
        }
    );

    el("applyPower").addEventListener(
        "click",
        async () => {
            try {
                await post("/api/control", {
                    power: Number(
                        el("powerSlider").value
                    )
                });

                message("Potencia aplicada");

            } catch (err) {
                message(err.message, true);
            }
        }
    );

    // MODOS DE OPERACION

    for (const [id, mode] of [
        ["manualMode", "manual"],
        ["autoMode", "automatico"]
    ]) {
        el(id).addEventListener(
            "click",
            async () => {
                try {
                    await post("/api/mode", {
                        mode: mode
                    });

                    updateMode(mode);

                    message(
                        `Modo ${mode} activado`
                    );

                } catch (err) {
                    message(err.message, true);
                }
            }
        );
    }

    // CONFIGURACION PID

    el("pidForm").addEventListener(
        "submit",
        async event => {
            event.preventDefault();

            try {
                await post("/api/pid", {
                    setpoint: Number(
                        el("setpoint").value
                    ),

                    kp: Number(
                        el("kp").value
                    ),

                    ki: Number(
                        el("ki").value
                    ),

                    kd: Number(
                        el("kd").value
                    )
                });

                message(
                    "Parámetros PID guardados"
                );

            } catch (err) {
                message(err.message, true);
            }
        }
    );

    // CARGAR CONFIGURACION

    try {
        const config = await request("/api/pid");

        el("setpoint").value =
            config.setpoint_c;

        el("kp").value = config.kp;
        el("ki").value = config.ki;
        el("kd").value = config.kd;

        updateMode(config.mode);

    } catch (err) {
        message(err.message, true);
    }

    await refreshStatus();
    await refreshStats();

    setInterval(refreshStatus, 1000);
    setInterval(refreshStats, 5000);
}


document.addEventListener(
    "DOMContentLoaded",
    init
);
