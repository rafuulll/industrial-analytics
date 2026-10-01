"""Executa o pipeline completo. Uso: py src/main.py"""
import pandas as pd

import analysis
import anomalies
import config as cfg
import generate_data
import transform


def save(df, name):
    df = df.copy()
    for col in df.columns:
        if col == "date" or col.startswith("first_"):
            df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")
    df.to_csv(cfg.PROCESSED_DIR / name, index=False, float_format="%.4f",
              date_format="%Y-%m-%d %H:%M:%S")


def run():
    cfg.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    generate_data.main()
    raw = pd.read_csv(cfg.RAW_DIR / "production_hourly_raw.csv")
    machines = pd.read_csv(cfg.RAW_DIR / "machines.csv")

    fact, kpi_daily, clean_report = transform.main(raw, machines)
    print(f"[transform] {clean_report}")

    limits, alerts, summary = anomalies.main(fact, kpi_daily)
    print(f"[anomalies] {len(alerts):,} alertas")
    print(summary.to_string(index=False))

    save(fact, "fact_production.csv")
    save(machines, "dim_machine.csv")
    save(kpi_daily, "kpi_daily.csv")
    save(limits, "control_limits.csv")
    save(alerts, "alerts.csv")
    save(summary, "early_warning.csv")

    analysis.main(fact, kpi_daily, limits, alerts, summary, clean_report)


if __name__ == "__main__":
    run()
