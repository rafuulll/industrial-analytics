"""
Detecção em duas camadas:
1. limite fixo nas leituras horárias
2. carta de controle (média +/- 3 desvios) nos indicadores diários de cada máquina
"""
import pandas as pd

import config as cfg


def fixed_limit_alerts(fact):
    rows = []
    for variable, limit in cfg.FIXED_LIMITS.items():
        hit = fact[fact[variable] > limit]
        rows.append(pd.DataFrame({
            "timestamp": hit["timestamp"],
            "date": hit["date"],
            "machine_id": hit["machine_id"],
            "rule": "limite_fixo",
            "category": "sinal",
            "variable": variable,
            "value": hit[variable],
            "limit": limit,
        }))
    return pd.concat(rows, ignore_index=True)


def control_limits(kpi_daily):
    # Só o período estável entra no cálculo; com os 90 dias, o próprio problema
    # aumentaria o desvio padrão e abriria os limites.
    first_day = kpi_daily["date"].min()
    baseline = kpi_daily[kpi_daily["date"] < first_day + pd.Timedelta(days=cfg.BASELINE_DAYS)]
    rows = []
    for machine_id, group in baseline.groupby("machine_id"):
        for variable in cfg.CONTROL_VARIABLES:
            mean, std = group[variable].mean(), group[variable].std()
            rows.append(dict(machine_id=machine_id, variable=variable, mean=mean, std=std,
                             lcl=mean - cfg.SIGMA_K * std, ucl=mean + cfg.SIGMA_K * std))
    return pd.DataFrame(rows)


def control_chart_alerts(kpi_daily, limits):
    first_day = kpi_daily["date"].min()
    monitored = kpi_daily[kpi_daily["date"] >= first_day + pd.Timedelta(days=cfg.BASELINE_DAYS)]
    rows = []
    for variable, spec in cfg.CONTROL_VARIABLES.items():
        lim = limits[limits["variable"] == variable][["machine_id", "lcl", "ucl"]]
        merged = monitored[["date", "machine_id", variable]].merge(lim, on="machine_id")
        if spec["side"] == "upper":
            hit = merged[merged[variable] > merged["ucl"]]
            limit_value = hit["ucl"]
        else:
            hit = merged[merged[variable] < merged["lcl"]]
            limit_value = hit["lcl"]
        rows.append(pd.DataFrame({
            "timestamp": hit["date"],
            "date": hit["date"],
            "machine_id": hit["machine_id"],
            "rule": "carta_controle",
            "category": spec["category"],
            "variable": variable,
            "value": hit[variable],
            "limit": limit_value,
        }))
    return pd.concat(rows, ignore_index=True)


def first_confirmed_date(dates, confirm_days=cfg.CONFIRM_DAYS):
    """Primeiro dia de uma sequência de `confirm_days` dias seguidos fora do limite."""
    days = sorted(pd.to_datetime(dates).unique())
    run_start, run_len, previous = None, 0, None
    for d in days:
        if previous is not None and d - previous == pd.Timedelta(days=1):
            run_len += 1
        else:
            run_start, run_len = d, 1
        if run_len >= confirm_days:
            return run_start
        previous = d
    return pd.NaT


def early_warning_summary(alerts):
    rows = []
    for machine_id, group in alerts.groupby("machine_id"):
        chart = group[group["rule"] == "carta_controle"]
        signal = first_confirmed_date(chart.loc[chart["category"] == "sinal", "date"])
        impact = first_confirmed_date(chart.loc[chart["category"] == "impacto", "date"])
        fixed = group.loc[group["rule"] == "limite_fixo", "date"].min()
        lead = (impact - signal).days if pd.notna(signal) and pd.notna(impact) else None
        rows.append(dict(machine_id=machine_id, first_signal=signal, first_impact=impact,
                         first_fixed_limit=fixed, lead_time_days=lead))
    return pd.DataFrame(rows)


def main(fact, kpi_daily):
    limits = control_limits(kpi_daily)
    alerts = pd.concat([fixed_limit_alerts(fact), control_chart_alerts(kpi_daily, limits)],
                       ignore_index=True).sort_values(["timestamp", "machine_id"])
    summary = early_warning_summary(alerts)
    return limits, alerts.reset_index(drop=True), summary
