import numpy as np
import pandas as pd
import pytest

import anomalies
import config as cfg


def daily_series(values, machine_id="X"):
    n = len(values)
    return pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=n, freq="D"),
        "machine_id": machine_id,
        "temperature_mean": values,
        "vibration_mean": 2.0,
        "oee": 0.80,
        "defect_rate": 0.012,
    })


def test_first_confirmed_date_requires_consecutive_days():
    dates = pd.to_datetime(["2026-02-01", "2026-02-05", "2026-02-06", "2026-02-07"])
    assert anomalies.first_confirmed_date(dates, confirm_days=2) == pd.Timestamp("2026-02-05")


def test_first_confirmed_date_returns_nat_when_never_confirmed():
    dates = pd.to_datetime(["2026-02-01", "2026-02-03"])
    assert pd.isna(anomalies.first_confirmed_date(dates, confirm_days=2))


def test_control_chart_flags_only_the_shift_after_baseline():
    rng = np.random.default_rng(0)
    stable = 60 + rng.normal(0, 0.3, cfg.BASELINE_DAYS + 10)
    shifted = 60 + 5 + rng.normal(0, 0.3, 10)
    kpi = daily_series(np.concatenate([stable, shifted]))
    limits = anomalies.control_limits(kpi)
    alerts = anomalies.control_chart_alerts(kpi, limits)
    temp_alerts = alerts[alerts["variable"] == "temperature_mean"]
    shift_start = kpi["date"].iloc[cfg.BASELINE_DAYS + 10]
    assert len(temp_alerts) == 10
    assert (temp_alerts["date"] >= shift_start).all()


def test_limits_come_only_from_baseline_period():
    values = [60.0] * cfg.BASELINE_DAYS + [90.0] * 30
    kpi = daily_series(values)
    kpi.loc[: cfg.BASELINE_DAYS - 1, "temperature_mean"] += np.tile([-0.5, 0.5], cfg.BASELINE_DAYS // 2)
    limits = anomalies.control_limits(kpi).set_index("variable")
    assert limits.loc["temperature_mean", "mean"] == pytest.approx(60.0)
