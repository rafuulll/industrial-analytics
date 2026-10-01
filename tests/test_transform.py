import numpy as np
import pandas as pd
import pytest

import transform

MACHINES = pd.DataFrame({"machine_id": ["X"], "ideal_rate_per_min": [2.0]})


def make_raw(rows):
    cols = ["timestamp", "machine_id", "shift", "planned_minutes", "downtime_minutes",
            "downtime_reason", "units_produced", "defective_units", "temperature_c",
            "vibration_mm_s", "energy_kwh", "maintenance_flag"]
    return pd.DataFrame(rows, columns=cols)


def base_row(hour, **overrides):
    row = dict(timestamp=f"2026-01-01 {hour:02d}:00:00", machine_id="X", shift="A",
               planned_minutes=60, downtime_minutes=0, downtime_reason="",
               units_produced=100, defective_units=2, temperature_c=60.0,
               vibration_mm_s=2.0, energy_kwh=15.0, maintenance_flag=0)
    row.update(overrides)
    return list(row.values())


def test_clean_handles_duplicates_invalid_sensor_and_negative_production():
    raw = make_raw([
        base_row(6),
        base_row(6),
        base_row(7, temperature_c=999.0),
        base_row(8, units_produced=-100),
        base_row(9),
    ])
    df, report = transform.clean(raw)
    assert report["duplicatas_removidas"] == 1
    assert report["leituras_invalidas"] == 1
    assert report["registros_producao_invalidos_removidos"] == 1
    assert len(df) == 3
    assert df["temperature_c"].max() == pytest.approx(60.0)


def test_oee_components_with_known_numbers():
    # 60 min planejados, 12 parados -> 48 operando
    # 80 peças a 2 peças/min = 40 min ideais -> performance 40/48
    # 4 defeitos -> 76 boas -> qualidade 76/80
    raw = make_raw([base_row(6, downtime_minutes=12, units_produced=80, defective_units=4)])
    df, _ = transform.clean(raw)
    fact = transform.add_derived_columns(df, MACHINES)
    k = transform.compute_kpis(fact, ["machine_id"]).iloc[0]
    assert k["availability"] == pytest.approx(48 / 60)
    assert k["performance"] == pytest.approx(40 / 48)
    assert k["quality"] == pytest.approx(76 / 80)
    assert k["oee"] == pytest.approx((48 / 60) * (40 / 48) * (76 / 80))
    assert k["oee"] == pytest.approx((76 / 2) / 60)


def test_ratio_kpis_use_sums_not_mean_of_percentages():
    # hora 1: 10 peças, 5 defeitos (50%); hora 2: 190 peças, 0 defeitos (0%)
    # média dos percentuais seria 25%; o correto é 5/200 = 2,5%
    raw = make_raw([base_row(6, units_produced=10, defective_units=5),
                    base_row(7, units_produced=190, defective_units=0)])
    df, _ = transform.clean(raw)
    fact = transform.add_derived_columns(df, MACHINES)
    k = transform.compute_kpis(fact, ["machine_id"]).iloc[0]
    assert k["defect_rate"] == pytest.approx(5 / 200)


def test_zero_planned_time_does_not_break_kpis():
    raw = make_raw([base_row(6, planned_minutes=0, units_produced=0, defective_units=0)])
    df, _ = transform.clean(raw)
    fact = transform.add_derived_columns(df, MACHINES)
    k = transform.compute_kpis(fact, ["machine_id"]).iloc[0]
    assert np.isnan(k["availability"])
