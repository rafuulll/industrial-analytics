"""Gráficos e resumo numérico (reports/summary.md) usados no README."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

import config as cfg
from transform import compute_kpis

SURFACE, INK, INK_2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
BLUE, ORANGE, CRITICAL, GRAY = "#2a78d6", "#eb6834", "#d03b3b", "#c3c2b7"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRAY, "axes.labelcolor": INK_2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "lines.linewidth": 2, "axes.axisbelow": True,
})


def pct(x, digits=1):
    return f"{x * 100:.{digits}f}%".replace(".", ",")


def num(x, digits=0):
    s = f"{x:,.{digits}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(cfg.FIGURES_DIR / name, dpi=150)
    plt.close(fig)


def _md_table(df):
    header = "| " + " | ".join(df.columns) + " |"
    sep = "| " + " | ".join("---" for _ in df.columns) + " |"
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, sep, *rows])


def fig_machines(by_machine):
    d = by_machine.sort_values("machine_id", ascending=False)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    axes[0].barh(d["machine_id"], d["good_units"] / 1000, color=BLUE, height=0.6)
    axes[0].set_title("Peças boas no período (mil)")
    for y, v in zip(d["machine_id"], d["good_units"] / 1000):
        axes[0].text(v, y, f" {num(v, 1)}", va="center", color=INK_2)
    axes[1].barh(d["machine_id"], d["oee"] * 100, color=BLUE, height=0.6)
    axes[1].set_title("OEE no período (%)")
    axes[1].set_xlim(0, 100)
    for y, v in zip(d["machine_id"], d["oee"]):
        axes[1].text(v * 100, y, f" {pct(v)}", va="center", color=INK_2)
    for ax in axes:
        ax.grid(axis="y", visible=False)
    fig.suptitle("Qual máquina produz mais? E qual usa melhor o tempo disponível?",
                 x=0.01, ha="left", fontweight="bold")
    _save(fig, "fig01_maquinas_producao_oee.png")


def fig_pareto(fact):
    stops = (fact[fact["downtime_minutes"] > 0]
             .groupby("downtime_reason")["downtime_minutes"].sum()
             .sort_values(ascending=False) / 60)
    pareto = stops.to_frame("horas")
    pareto["acumulado"] = pareto["horas"].cumsum() / pareto["horas"].sum()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(range(len(pareto)), pareto["horas"], color=BLUE, width=0.6)
    for i, (h, c) in enumerate(zip(pareto["horas"], pareto["acumulado"])):
        ax.text(i, h, f"{num(h)} h\nacum. {pct(c, 0)}", ha="center", va="bottom", color=INK_2)
    ax.set_xticks(range(len(pareto)), pareto.index)
    ax.set_ylabel("Horas paradas (5 máquinas)")
    ax.set_ylim(0, pareto["horas"].max() * 1.25)
    ax.grid(axis="x", visible=False)
    ax.set_title("Pareto de paradas: onde está o tempo perdido?")
    _save(fig, "fig02_pareto_paradas.png")
    return pareto


def _event_chart(kpi_daily, limits, summary, machine_id, top_var, top_label,
                 bottom_var, bottom_label, title, filename):
    """Sinal do sensor em cima, impacto na produção embaixo."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    d = kpi_daily[kpi_daily["machine_id"] == machine_id]
    lim = limits[limits["machine_id"] == machine_id].set_index("variable")
    s = summary.set_index("machine_id").loc[machine_id]
    start = d["date"].min()
    base_end = start + pd.Timedelta(days=cfg.BASELINE_DAYS)
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True)
    for ax, var, label, scale in [(axes[0], top_var, top_label, 1),
                                  (axes[1], bottom_var, bottom_label, 100)]:
        side = "lcl" if cfg.CONTROL_VARIABLES[var]["side"] == "lower" else "ucl"
        ax.axvspan(start, base_end, color=GRID, alpha=0.5, lw=0)
        ax.plot(d["date"], d[var] * scale, color=BLUE, label="valor diário")
        ax.axhline(lim.loc[var, "mean"] * scale, color=MUTED, lw=1, ls="--", label="média de referência")
        ax.axhline(lim.loc[var, side] * scale, color=CRITICAL, lw=1.2, label="limite de controle (3σ)")
        ax.set_ylabel(label)
    axes[0].legend(loc="upper left", frameon=False, fontsize=9)

    marks = [(s["first_signal"], "1º sinal confirmado (carta)", BLUE),
             (s["first_fixed_limit"], f"1º alerta do limite fixo (leitura horária)", ORANGE),
             (s["first_impact"], "impacto confirmado", CRITICAL)]
    pm = cfg.PLANNED_MAINTENANCE
    if machine_id == pm["machine_id"]:
        marks.append((start + pd.Timedelta(days=pm["day"]), "manutenção", INK_2))
    handles = [Patch(color=GRID, label="período de referência")]
    for date, text, color in marks:
        if pd.notna(date):
            for ax in axes:
                ax.axvline(date, color=color, lw=1.2, ls=":")
            handles.append(Line2D([], [], color=color, lw=1.2, ls=":", label=text))
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=9)
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    axes[0].set_title(title)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(cfg.FIGURES_DIR / filename, dpi=150)
    plt.close(fig)


def fig_shifts(by_shift):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    axes[0].bar(by_shift["shift"], by_shift["oee"] * 100, color=BLUE, width=0.5)
    axes[0].set_title("OEE por turno (%)")
    axes[0].set_ylim(0, 100)
    axes[1].bar(by_shift["shift"], by_shift["defect_rate"] * 100, color=BLUE, width=0.5)
    axes[1].set_title("Taxa de defeitos por turno (%)")
    axes[1].set_ylim(0, by_shift["defect_rate"].max() * 100 * 1.2)
    for ax, col in [(axes[0], "oee"), (axes[1], "defect_rate")]:
        for x, v in zip(by_shift["shift"], by_shift[col]):
            ax.text(x, v * 100, pct(v, 2 if col == "defect_rate" else 1), ha="center",
                    va="bottom", color=INK_2)
        ax.grid(axis="x", visible=False)
        ax.set_xlabel("Turno (A 06-14h, B 14-22h, C 22-06h)")
    _save(fig, "fig05_turnos.png")


def fig_relations(kpi_daily):
    r_temp = kpi_daily["temperature_mean"].corr(kpi_daily["downtime_minutes"])
    r_vib = kpi_daily["vibration_mean"].corr(kpi_daily["defect_rate"])
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    axes[0].scatter(kpi_daily["temperature_mean"], kpi_daily["downtime_minutes"] / 60,
                    s=14, color=BLUE, alpha=0.5, lw=0)
    axes[0].set_xlabel("Temperatura média do dia (°C)")
    axes[0].set_ylabel("Horas paradas no dia")
    axes[0].set_title(f"Temperatura x paradas (r = {r_temp:.2f})".replace(".", ","))
    axes[1].scatter(kpi_daily["vibration_mean"], kpi_daily["defect_rate"] * 100,
                    s=14, color=BLUE, alpha=0.5, lw=0)
    axes[1].set_xlabel("Vibração média do dia (mm/s)")
    axes[1].set_ylabel("Taxa de defeitos (%)")
    axes[1].set_title(f"Vibração x defeitos (r = {r_vib:.2f})".replace(".", ","))
    fig.text(0.01, 0.01, "Cada ponto = uma máquina em um dia. r = correlação de Pearson.",
             color=MUTED, fontsize=8)
    _save(fig, "fig06_relacoes.png")
    return {"temp_downtime": r_temp, "vib_defects": r_vib}


def fig_energy(by_machine):
    d = by_machine.sort_values("machine_id", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.barh(d["machine_id"], d["energy_per_good_unit"], color=BLUE, height=0.6)
    for y, v in zip(d["machine_id"], d["energy_per_good_unit"]):
        ax.text(v, y, f" {num(v, 3)} kWh", va="center", color=INK_2)
    ax.set_xlim(0, d["energy_per_good_unit"].max() * 1.2)
    ax.grid(axis="y", visible=False)
    ax.set_title("Energia por peça boa (kWh/peça): qual máquina é menos eficiente?")
    _save(fig, "fig07_energia_por_peca.png")


def main(fact, kpi_daily, limits, alerts, summary, clean_report):
    cfg.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    by_machine = compute_kpis(fact, ["machine_id"])
    by_shift = compute_kpis(fact, ["shift"])
    overall = compute_kpis(fact.assign(all="total"), ["all"]).iloc[0]

    fig_machines(by_machine)
    pareto = fig_pareto(fact)
    _event_chart(kpi_daily, limits, summary, "M3", "temperature_mean", "Temperatura média (°C)",
                 "oee", "OEE diário (%)",
                 "M3: a temperatura sobe antes de o OEE cair?", "fig03_m3_temperatura_oee.png")
    _event_chart(kpi_daily, limits, summary, "M4", "vibration_mean", "Vibração média (mm/s)",
                 "defect_rate", "Taxa de defeitos (%)",
                 "M4: a vibração sobe antes de os defeitos aumentarem?", "fig04_m4_vibracao_defeitos.png")
    fig_shifts(by_shift)
    corr = fig_relations(kpi_daily)
    fig_energy(by_machine)

    # M3: 14 dias antes x 14 dias depois da manutenção
    pm = cfg.PLANNED_MAINTENANCE
    pm_date = kpi_daily["date"].min() + pd.Timedelta(days=pm["day"])
    m3 = fact[fact["machine_id"] == pm["machine_id"]]
    before = compute_kpis(m3[(m3["date"] >= pm_date - pd.Timedelta(days=14)) & (m3["date"] < pm_date)]
                          .assign(p="antes"), ["p"])
    after = compute_kpis(m3[(m3["date"] > pm_date) & (m3["date"] <= pm_date + pd.Timedelta(days=14))]
                         .assign(p="depois"), ["p"])
    january = compute_kpis(m3[m3["date"] < kpi_daily["date"].min() + pd.Timedelta(days=cfg.BASELINE_DAYS)]
                           .assign(p="referência"), ["p"])
    ba = pd.concat([january, before, after])

    m4 = fact[fact["machine_id"] == "M4"]
    m4_last = compute_kpis(m4[m4["date"] > kpi_daily["date"].max() - pd.Timedelta(days=14)]
                           .assign(p="últimos 14 dias"), ["p"])
    m4_ref = compute_kpis(m4[m4["date"] < kpi_daily["date"].min() + pd.Timedelta(days=cfg.BASELINE_DAYS)]
                          .assign(p="referência"), ["p"])

    alert_counts = (alerts.assign(n=1)
                    .pivot_table(index="machine_id", columns="rule", values="n", aggfunc="sum", fill_value=0)
                    .reindex([m["machine_id"] for m in cfg.MACHINES], fill_value=0))

    start = kpi_daily["date"].min()
    validation = []
    for ev in cfg.INJECTED_EVENTS:
        s = summary.set_index("machine_id").loc[ev["machine_id"]]
        injected = start + pd.Timedelta(days=ev["start_day"])
        validation.append({
            "Máquina": ev["machine_id"],
            "Problema simulado": ev["description"],
            "Início simulado": injected.strftime("%d/%m"),
            "1º sinal (carta)": s["first_signal"].strftime("%d/%m"),
            "Limite fixo": s["first_fixed_limit"].strftime("%d/%m"),
            "Impacto confirmado": s["first_impact"].strftime("%d/%m"),
            "Aviso antecipado": f"{int(s['lead_time_days'])} dias",
            "Carta x limite fixo": f"{(s['first_fixed_limit'] - s['first_signal']).days} dias antes",
        })

    t_mach = pd.DataFrame({
        "Máquina": by_machine["machine_id"],
        "Peças boas": by_machine["good_units"].map(num),
        "Meta atingida": by_machine["target_attainment"].map(pct),
        "Disponib.": by_machine["availability"].map(pct),
        "Performance": by_machine["performance"].map(pct),
        "Qualidade": by_machine["quality"].map(pct),
        "OEE": by_machine["oee"].map(pct),
        "Defeitos": by_machine["defect_rate"].map(lambda v: pct(v, 2)),
        "Horas paradas": (by_machine["downtime_minutes"] / 60).map(num),
        "kWh/peça boa": by_machine["energy_per_good_unit"].map(lambda v: num(v, 3)),
    })
    t_shift = pd.DataFrame({
        "Turno": by_shift["shift"], "OEE": by_shift["oee"].map(pct),
        "Performance": by_shift["performance"].map(pct),
        "Defeitos": by_shift["defect_rate"].map(lambda v: pct(v, 2)),
    })
    t_pareto = pd.DataFrame({"Motivo": pareto.index, "Horas": pareto["horas"].map(num),
                             "Acumulado": pareto["acumulado"].map(lambda v: pct(v, 0))})
    t_ba = pd.DataFrame({"Período (M3)": ba["p"], "Temp. média (°C)": ba["temperature_mean"].map(lambda v: num(v, 1)),
                         "Disponib.": ba["availability"].map(pct), "OEE": ba["oee"].map(pct)})
    t_m4 = pd.concat([m4_ref, m4_last])
    t_m4 = pd.DataFrame({"Período (M4)": t_m4["p"], "Vibração (mm/s)": t_m4["vibration_mean"].map(lambda v: num(v, 2)),
                         "Defeitos": t_m4["defect_rate"].map(lambda v: pct(v, 2)), "OEE": t_m4["oee"].map(pct)})
    t_alerts = alert_counts.reset_index().rename(columns={
        "machine_id": "Máquina", "carta_controle": "Dias fora do limite (carta)",
        "limite_fixo": "Horas acima do limite fixo"})

    lines = [
        "# Resultados gerados automaticamente",
        "",
        "Arquivo criado por `src/analysis.py`. Dados 100% sintéticos.",
        "",
        "## Qualidade dos dados (limpeza)",
        "",
        _md_table(pd.DataFrame({"Etapa": list(clean_report), "Quantidade": [num(v) for v in clean_report.values()]})),
        "",
        "## Visão geral (5 máquinas, 90 dias)",
        "",
        f"- Peças boas: {num(overall['good_units'])}",
        f"- OEE geral: {pct(overall['oee'])} (Disponibilidade {pct(overall['availability'])} x "
        f"Performance {pct(overall['performance'])} x Qualidade {pct(overall['quality'])})",
        f"- Taxa de defeitos: {pct(overall['defect_rate'], 2)}",
        f"- Horas paradas: {num(overall['downtime_minutes'] / 60)}",
        f"- Meta atingida: {pct(overall['target_attainment'])}",
        "",
        "## Por máquina",
        "",
        _md_table(t_mach),
        "",
        "## Por turno",
        "",
        _md_table(t_shift),
        "",
        "## Pareto de paradas",
        "",
        _md_table(t_pareto),
        "",
        "## Correlações (máquina-dia)",
        "",
        f"- Temperatura média x horas paradas: r = {corr['temp_downtime']:.2f}".replace(".", ","),
        f"- Vibração média x taxa de defeitos: r = {corr['vib_defects']:.2f}".replace(".", ","),
        "",
        "## Alertas por máquina",
        "",
        _md_table(t_alerts),
        "",
        "## Aviso antecipado: detecção x problema simulado",
        "",
        _md_table(pd.DataFrame(validation)),
        "",
        "## M3: antes e depois da manutenção",
        "",
        _md_table(t_ba),
        "",
        "## M4: situação no fim do período",
        "",
        _md_table(t_m4),
        "",
    ]
    (cfg.REPORTS_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("[analysis] 7 gráficos em reports/figures/ e números em reports/summary.md")
