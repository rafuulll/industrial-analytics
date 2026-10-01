"""Limpeza dos dados brutos e cálculo dos KPIs de produção."""
import numpy as np
import pandas as pd

import config as cfg


def clean(raw):
    df = raw.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["downtime_reason"] = df["downtime_reason"].fillna("")
    report = {"linhas_brutas": len(df)}

    before = len(df)
    df = df.drop_duplicates()
    report["duplicatas_removidas"] = before - len(df)

    report["leituras_invalidas"] = 0
    for col, (low, high) in cfg.VALID_RANGES.items():
        invalid = (df[col] < low) | (df[col] > high)
        report["leituras_invalidas"] += int(invalid.sum())
        df.loc[invalid, col] = np.nan

    bad_production = ((df["units_produced"] < 0) | (df["defective_units"] < 0)
                      | (df["defective_units"] > df["units_produced"])
                      | (df["downtime_minutes"] > df["planned_minutes"]))
    report["registros_producao_invalidos_removidos"] = int(bad_production.sum())
    df = df[~bad_production]

    # temperatura e vibração mudam devagar: interpolar dentro de cada máquina é seguro
    df = df.sort_values(["machine_id", "timestamp"])
    sensor_cols = list(cfg.VALID_RANGES)
    report["leituras_sensor_interpoladas"] = int(df[sensor_cols].isna().sum().sum())
    df[sensor_cols] = (df.groupby("machine_id")[sensor_cols]
                         .transform(lambda s: s.interpolate(limit=3, limit_direction="both")))

    df = df.sort_values(["timestamp", "machine_id"]).reset_index(drop=True)
    report["linhas_finais"] = len(df)
    return df, report


def add_derived_columns(df, machines):
    df = df.merge(machines[["machine_id", "ideal_rate_per_min"]], on="machine_id", how="left")
    rate = df["ideal_rate_per_min"]
    df["date"] = df["timestamp"].dt.normalize()
    df["operating_minutes"] = df["planned_minutes"] - df["downtime_minutes"]
    df["good_units"] = df["units_produced"] - df["defective_units"]
    df["ideal_minutes"] = df["units_produced"] / rate
    df["good_minutes"] = df["good_units"] / rate
    df["target_units"] = rate * df["planned_minutes"] * cfg.TARGET_FACTOR
    return df.drop(columns="ideal_rate_per_min")


def _ratio(num, den):
    return num / den.replace(0, np.nan)


def compute_kpis(df, by):
    # Razões sempre como soma/soma. Média de percentuais daria o mesmo peso
    # para uma hora com 10 peças e outra com 170.
    sums = df.groupby(by).agg(
        planned_minutes=("planned_minutes", "sum"),
        downtime_minutes=("downtime_minutes", "sum"),
        operating_minutes=("operating_minutes", "sum"),
        ideal_minutes=("ideal_minutes", "sum"),
        good_minutes=("good_minutes", "sum"),
        units_produced=("units_produced", "sum"),
        defective_units=("defective_units", "sum"),
        good_units=("good_units", "sum"),
        target_units=("target_units", "sum"),
        energy_kwh=("energy_kwh", "sum"),
        temperature_mean=("temperature_c", "mean"),
        vibration_mean=("vibration_mm_s", "mean"),
    ).reset_index()

    sums["availability"] = _ratio(sums["operating_minutes"], sums["planned_minutes"])
    sums["performance"] = _ratio(sums["ideal_minutes"], sums["operating_minutes"])
    # ponderada pelo tempo ideal para que A x P x Q feche certo com máquinas de velocidades diferentes
    sums["quality"] = _ratio(sums["good_minutes"], sums["ideal_minutes"])
    sums["oee"] = sums["availability"] * sums["performance"] * sums["quality"]
    sums["defect_rate"] = _ratio(sums["defective_units"], sums["units_produced"])
    sums["target_attainment"] = _ratio(sums["good_units"], sums["target_units"])
    sums["energy_per_good_unit"] = _ratio(sums["energy_kwh"], sums["good_units"])
    return sums


def main(raw, machines):
    df, report = clean(raw)
    fact = add_derived_columns(df, machines)
    kpi_daily = compute_kpis(fact, ["date", "machine_id"])
    return fact, kpi_daily, report
