import pandas as pd
import pytest

import anomalies
import config as cfg
import generate_data
import transform


@pytest.fixture(scope="module")
def pipeline():
    raw, machines = generate_data.generate()
    fact, kpi_daily, report = transform.main(raw, machines)
    limits, alerts, summary = anomalies.main(fact, kpi_daily)
    return dict(raw=raw, fact=fact, kpi_daily=kpi_daily, report=report, summary=summary)


def test_generation_is_reproducible():
    a, _ = generate_data.generate(seed=123)
    b, _ = generate_data.generate(seed=123)
    pd.testing.assert_frame_equal(a, b)


def test_cleaning_removes_all_injected_issues(pipeline):
    report, fact = pipeline["report"], pipeline["fact"]
    assert report["duplicatas_removidas"] == cfg.N_DUPLICATED_ROWS
    assert report["leituras_invalidas"] >= cfg.N_SENSOR_ERROR_CODES
    assert not fact.duplicated(["timestamp", "machine_id"]).any()
    assert (fact["units_produced"] >= 0).all()
    assert fact[["temperature_c", "vibration_mm_s"]].notna().all().all()


def test_daily_kpis_are_valid_percentages(pipeline):
    kpi = pipeline["kpi_daily"]
    for col in ["availability", "performance", "quality", "oee"]:
        assert kpi[col].between(0, 1).all(), col


def test_injected_problems_are_detected_after_they_start(pipeline):
    summary = pipeline["summary"].set_index("machine_id")
    start = pd.Timestamp(cfg.START_DATE)
    for event in cfg.INJECTED_EVENTS:
        row = summary.loc[event["machine_id"]]
        injected = start + pd.Timedelta(days=event["start_day"])
        assert row["first_signal"] >= injected
        assert row["first_impact"] > row["first_signal"]


def test_healthy_machine_has_no_confirmed_alert(pipeline):
    summary = pipeline["summary"].set_index("machine_id")
    assert "M1" not in summary.index or (
        pd.isna(summary.loc["M1", "first_signal"]) and pd.isna(summary.loc["M1", "first_impact"]))
