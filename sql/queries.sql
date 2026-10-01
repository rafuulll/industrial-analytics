-- Tabelas: fact_production (máquina x hora), kpi_daily (máquina x dia), dim_machine, alerts, control_limits

-- Q1. Qual máquina produz mais e qual tem a maior taxa de defeitos?
SELECT
    machine_id,
    SUM(good_units)                                        AS pecas_boas,
    ROUND(100.0 * SUM(defective_units) / SUM(units_produced), 2) AS taxa_defeitos_pct,
    ROUND(SUM(downtime_minutes) / 60.0, 0)                 AS horas_paradas
FROM fact_production
GROUP BY machine_id
ORDER BY pecas_boas DESC;

-- Q2. OEE por máquina (soma/soma dos componentes)
SELECT
    machine_id,
    ROUND(100.0 * SUM(operating_minutes) / SUM(planned_minutes), 1) AS disponibilidade_pct,
    ROUND(100.0 * SUM(ideal_minutes) / SUM(operating_minutes), 1)   AS performance_pct,
    ROUND(100.0 * SUM(good_minutes) / SUM(ideal_minutes), 1)        AS qualidade_pct,
    ROUND(100.0 * SUM(good_minutes) / SUM(planned_minutes), 1)      AS oee_pct
FROM fact_production
GROUP BY machine_id
ORDER BY oee_pct DESC;

-- Q3. Qual turno tem melhor desempenho?
SELECT
    shift                                                  AS turno,
    ROUND(100.0 * SUM(good_minutes) / SUM(planned_minutes), 1)      AS oee_pct,
    ROUND(100.0 * SUM(defective_units) / SUM(units_produced), 2)    AS taxa_defeitos_pct
FROM fact_production
GROUP BY shift
ORDER BY oee_pct DESC;

-- Q4. Pareto de paradas com percentual acumulado
WITH por_motivo AS (
    SELECT downtime_reason AS motivo, SUM(downtime_minutes) / 60.0 AS horas
    FROM fact_production
    WHERE downtime_minutes > 0
    GROUP BY downtime_reason
)
SELECT
    motivo,
    ROUND(horas, 0)                                                        AS horas,
    ROUND(100.0 * horas / SUM(horas) OVER (), 1)                           AS participacao_pct,
    ROUND(100.0 * SUM(horas) OVER (ORDER BY horas DESC) / SUM(horas) OVER (), 1) AS acumulado_pct
FROM por_motivo
ORDER BY horas DESC;

-- Q5. Evolução semanal do OEE e da temperatura da M3
WITH semanal AS (
    SELECT
        strftime('%Y-%W', date)            AS semana,
        SUM(good_minutes)                  AS good_min,
        SUM(planned_minutes)               AS planned_min,
        AVG(temperature_c)                 AS temp_media
    FROM fact_production
    WHERE machine_id = 'M3'
    GROUP BY semana
)
SELECT semana,
       ROUND(100.0 * good_min / planned_min, 1) AS oee_pct,
       ROUND(temp_media, 1)                     AS temperatura_media
FROM semanal
ORDER BY semana;

-- Q6. Energia por peça de cada máquina comparada com a média da célula
WITH por_maquina AS (
    SELECT machine_id, SUM(energy_kwh) / SUM(good_units) AS kwh_por_peca
    FROM fact_production
    GROUP BY machine_id
)
SELECT machine_id,
       ROUND(kwh_por_peca, 3)                                        AS kwh_por_peca,
       ROUND(100.0 * (kwh_por_peca / AVG(kwh_por_peca) OVER () - 1), 1) AS diferenca_vs_media_pct
FROM por_maquina
ORDER BY kwh_por_peca DESC;

-- Q7. Média móvel de 7 dias da vibração da M4
SELECT
    date,
    ROUND(vibration_mean, 2) AS vibracao_dia,
    ROUND(AVG(vibration_mean) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2)
        AS vibracao_media_movel_7d
FROM kpi_daily
WHERE machine_id = 'M4'
ORDER BY date DESC
LIMIT 15;

-- Q8. Quantos dias cada máquina ficou fora dos limites de controle, por indicador?
SELECT machine_id, variable AS indicador, category AS tipo, COUNT(*) AS dias_fora_do_limite,
       MIN(date) AS primeiro_dia
FROM alerts
WHERE rule = 'carta_controle'
GROUP BY machine_id, variable, category
ORDER BY machine_id, primeiro_dia;

-- Q9. Os 10 piores dias (máquina x dia) em horas paradas
SELECT date, machine_id, ROUND(downtime_minutes / 60.0, 1) AS horas_paradas,
       ROUND(temperature_mean, 1) AS temperatura_media
FROM kpi_daily
ORDER BY downtime_minutes DESC
LIMIT 10;
