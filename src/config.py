from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

SEED = 42
START_DATE = "2026-01-01"
N_DAYS = 90

# turno C = 22h às 06h
SHIFT_HOURS = {"A": (6, 14), "B": (14, 22)}

MACHINES = [
    dict(machine_id="M1", machine_name="CNC 01", install_year=2021, ideal_rate_per_min=3.0,
         temp_base=60.0, vib_base=2.0, running_kw=15.0),
    dict(machine_id="M2", machine_name="CNC 02", install_year=2021, ideal_rate_per_min=3.0,
         temp_base=60.0, vib_base=2.0, running_kw=15.0),
    dict(machine_id="M3", machine_name="CNC 03", install_year=2017, ideal_rate_per_min=2.8,
         temp_base=60.0, vib_base=2.0, running_kw=15.0),
    dict(machine_id="M4", machine_name="CNC 04", install_year=2017, ideal_rate_per_min=2.8,
         temp_base=60.0, vib_base=2.0, running_kw=15.0),
    dict(machine_id="M5", machine_name="CNC 05", install_year=2010, ideal_rate_per_min=2.4,
         temp_base=62.0, vib_base=2.3, running_kw=16.0),
]
MACHINE_PUBLIC_COLUMNS = ["machine_id", "machine_name", "install_year", "ideal_rate_per_min"]

# Operação normal
P_STOP_PER_HOUR = 0.22
STOP_MEDIAN_MIN = 18
STOP_REASONS = ["Setup e troca de ferramenta", "Falta de material",
                "Falha mecânica", "Ajuste de qualidade"]
STOP_REASON_WEIGHTS = [0.40, 0.25, 0.20, 0.15]
PERFORMANCE_MEAN = 0.88
BASE_DEFECT_RATE = 0.012
IDLE_KW = 3.0
TARGET_FACTOR = 0.80

SHIFT_C_DEFECT_MULTIPLIER = 1.35
SHIFT_C_PERFORMANCE_FACTOR = 0.97

OVERHEAT_START_C = 66.0
OVERHEAT_P_PER_DEGREE = 0.03
VIB_DEFECT_START = 3.0
VIB_DEFECT_PER_UNIT = 0.03

# Problemas simulados (a detecção não usa estes valores)
INJECTED_EVENTS = [
    dict(machine_id="M3", variable="temperature_c", start_day=40, end_day=75, increase=18.0,
         description="Aquecimento gradual (ex.: falha de refrigeração), corrigido por manutenção no dia 75"),
    dict(machine_id="M4", variable="vibration_mm_s", start_day=55, end_day=None, increase=2.6,
         description="Vibração crescente (ex.: desgaste de rolamento), sem correção até o fim do período"),
]
PLANNED_MAINTENANCE = dict(machine_id="M3", day=75, start_hour=8, end_hour=16)

N_DUPLICATED_ROWS = 30
SENSOR_MISSING_FRACTION = 0.005
N_SENSOR_ERROR_CODES = 5
N_NEGATIVE_PRODUCTION = 3

# Detecção
VALID_RANGES = {"temperature_c": (0.0, 150.0), "vibration_mm_s": (0.0, 50.0)}
FIXED_LIMITS = {"temperature_c": 72.0, "vibration_mm_s": 4.0}
BASELINE_DAYS = 30
SIGMA_K = 3
CONFIRM_DAYS = 2

CONTROL_VARIABLES = {
    "temperature_mean": dict(side="upper", category="sinal"),
    "vibration_mean": dict(side="upper", category="sinal"),
    "oee": dict(side="lower", category="impacto"),
    "defect_rate": dict(side="upper", category="impacto"),
}
