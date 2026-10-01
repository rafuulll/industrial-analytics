"""Gera os dados sintéticos da célula de usinagem (1 linha = máquina x hora)."""
import numpy as np
import pandas as pd

import config as cfg


def _shift_from_hour(hours):
    a_start, a_end = cfg.SHIFT_HOURS["A"]
    b_start, b_end = cfg.SHIFT_HOURS["B"]
    return np.where((hours >= a_start) & (hours < a_end), "A",
                    np.where((hours >= b_start) & (hours < b_end), "B", "C"))


def _drift(day_frac, event):
    end = event["end_day"] if event["end_day"] is not None else cfg.N_DAYS
    progress = np.clip((day_frac - event["start_day"]) / (end - event["start_day"]), 0, 1)
    ramp = progress * event["increase"]
    if event["end_day"] is not None:
        ramp[day_frac >= event["end_day"]] = 0.0
    return ramp


def _simulate_machine(machine, timestamps, rng):
    n = len(timestamps)
    hours = timestamps.hour.to_numpy()
    day_frac = ((timestamps - timestamps[0]) / pd.Timedelta(days=1)).to_numpy()
    day = day_frac.astype(int)
    shift = _shift_from_hour(hours)
    is_c = shift == "C"

    planned = np.full(n, 60.0)
    maintenance = np.zeros(n, dtype=int)
    pm = cfg.PLANNED_MAINTENANCE
    if machine["machine_id"] == pm["machine_id"]:
        mask = (day == pm["day"]) & (hours >= pm["start_hour"]) & (hours < pm["end_hour"])
        planned[mask] = 0.0
        maintenance[mask] = 1

    temperature = (machine["temp_base"] + rng.normal(0, 0.4, cfg.N_DAYS)[day]
                   + rng.normal(0, 1.2, n) - 1.0 * is_c)
    vibration = machine["vib_base"] + rng.normal(0, 0.05, cfg.N_DAYS)[day] + rng.normal(0, 0.12, n)

    for event in cfg.INJECTED_EVENTS:
        if event["machine_id"] != machine["machine_id"]:
            continue
        if event["variable"] == "temperature_c":
            temperature = temperature + _drift(day_frac, event)
        elif event["variable"] == "vibration_mm_s":
            vibration = vibration + _drift(day_frac, event)

    base_stop = rng.random(n) < cfg.P_STOP_PER_HOUR
    base_duration = np.clip(rng.lognormal(np.log(cfg.STOP_MEDIAN_MIN), 0.6, n), 3, 55)
    base_reason = rng.choice(cfg.STOP_REASONS, p=cfg.STOP_REASON_WEIGHTS, size=n)
    downtime = np.where(base_stop, base_duration, 0.0)
    reason = np.where(base_stop, base_reason, "")

    # chance de parada por superaquecimento cresce com a temperatura
    p_overheat = np.clip(cfg.OVERHEAT_P_PER_DEGREE * (temperature - cfg.OVERHEAT_START_C), 0, 0.5)
    overheat = rng.random(n) < p_overheat
    overheat_duration = rng.uniform(15, 45, n)
    use_overheat = overheat & (overheat_duration > downtime)
    downtime = np.where(use_overheat, overheat_duration, downtime)
    reason = np.where(use_overheat, "Superaquecimento", reason)

    downtime = np.round(np.minimum(downtime, planned))
    reason = np.where(downtime > 0, reason, "")
    operating = planned - downtime

    performance = np.clip(rng.normal(cfg.PERFORMANCE_MEAN, 0.03, n), 0.6, 1.0)
    performance = performance * np.where(is_c, cfg.SHIFT_C_PERFORMANCE_FACTOR, 1.0)
    units = np.round(machine["ideal_rate_per_min"] * operating * performance).astype(int)

    defect_rate = (cfg.BASE_DEFECT_RATE * np.where(is_c, cfg.SHIFT_C_DEFECT_MULTIPLIER, 1.0)
                   + cfg.VIB_DEFECT_PER_UNIT * np.clip(vibration - cfg.VIB_DEFECT_START, 0, None))
    defective = rng.binomial(units, np.clip(defect_rate, 0, 1))

    energy = (machine["running_kw"] * operating / 60 + cfg.IDLE_KW * downtime / 60
              + rng.normal(0, 0.3, n))
    energy = np.clip(np.where(planned == 0, 0.2, energy), 0, None)

    return pd.DataFrame({
        "timestamp": timestamps,
        "machine_id": machine["machine_id"],
        "shift": shift,
        "planned_minutes": planned.astype(int),
        "downtime_minutes": downtime.astype(int),
        "downtime_reason": reason,
        "units_produced": units,
        "defective_units": defective,
        "temperature_c": np.round(temperature, 1),
        "vibration_mm_s": np.round(vibration, 2),
        "energy_kwh": np.round(energy, 2),
        "maintenance_flag": maintenance,
    })


def inject_data_issues(df, rng):
    """Insere erros comuns de dado bruto: sensor vazio, código 999, produção negativa e duplicatas."""
    df = df.copy()
    n = len(df)

    for col in ["temperature_c", "vibration_mm_s"]:
        idx = rng.choice(n, int(n * cfg.SENSOR_MISSING_FRACTION), replace=False)
        df.loc[idx, col] = np.nan

    idx = rng.choice(n, cfg.N_SENSOR_ERROR_CODES, replace=False)
    df.loc[idx, "temperature_c"] = 999.0

    candidates = df.index[df["units_produced"] > 0]
    idx = rng.choice(candidates, cfg.N_NEGATIVE_PRODUCTION, replace=False)
    df.loc[idx, "units_produced"] = -df.loc[idx, "units_produced"]

    dup = df.sample(cfg.N_DUPLICATED_ROWS, random_state=int(rng.integers(1_000_000)))
    df = pd.concat([df, dup], ignore_index=True)
    return df.sort_values(["timestamp", "machine_id"], kind="stable").reset_index(drop=True)


def generate(seed=cfg.SEED):
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(cfg.START_DATE, periods=cfg.N_DAYS * 24, freq="h")
    frames = [_simulate_machine(m, timestamps, rng) for m in cfg.MACHINES]
    clean = pd.concat(frames, ignore_index=True).sort_values(["timestamp", "machine_id"])
    raw = inject_data_issues(clean.reset_index(drop=True), rng)
    machines = pd.DataFrame(cfg.MACHINES)[cfg.MACHINE_PUBLIC_COLUMNS]
    return raw, machines


def main():
    cfg.RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw, machines = generate()
    raw.to_csv(cfg.RAW_DIR / "production_hourly_raw.csv", index=False)
    machines.to_csv(cfg.RAW_DIR / "machines.csv", index=False)
    print(f"[generate] {len(raw):,} linhas brutas em data/raw/")


if __name__ == "__main__":
    main()
