# Resultados gerados automaticamente

Arquivo criado por `src/analysis.py`. Dados 100% sintéticos.

## Qualidade dos dados (limpeza)

| Etapa | Quantidade |
| --- | --- |
| linhas_brutas | 10.830 |
| duplicatas_removidas | 30 |
| leituras_invalidas | 5 |
| registros_producao_invalidos_removidos | 3 |
| leituras_sensor_interpoladas | 112 |
| linhas_finais | 10.797 |

## Visão geral (5 máquinas, 90 dias)

- Peças boas: 1.431.643
- OEE geral: 79,0% (Disponibilidade 92,0% x Performance 87,1% x Qualidade 98,6%)
- Taxa de defeitos: 1,44%
- Horas paradas: 862
- Meta atingida: 98,7%

## Por máquina

| Máquina | Peças boas | Meta atingida | Disponib. | Performance | Qualidade | OEE | Defeitos | Horas paradas | kWh/peça boa |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | 307.980 | 99,1% | 92,1% | 87,2% | 98,7% | 79,2% | 1,35% | 170 | 0,099 |
| M2 | 309.637 | 99,5% | 92,8% | 87,0% | 98,7% | 79,6% | 1,35% | 156 | 0,099 |
| M3 | 280.136 | 96,9% | 90,1% | 87,1% | 98,7% | 77,5% | 1,31% | 213 | 0,106 |
| M4 | 287.178 | 99,0% | 92,5% | 87,2% | 98,1% | 79,2% | 1,88% | 161 | 0,106 |
| M5 | 246.712 | 99,2% | 92,5% | 87,0% | 98,7% | 79,4% | 1,33% | 162 | 0,131 |

## Por turno

| Turno | OEE | Performance | Defeitos |
| --- | --- | --- | --- |
| A | 80,0% | 87,9% | 1,31% |
| B | 79,9% | 88,0% | 1,33% |
| C | 77,0% | 85,3% | 1,71% |

## Pareto de paradas

| Motivo | Horas | Acumulado |
| --- | --- | --- |
| Setup e troca de ferramenta | 327 | 38% |
| Falta de material | 203 | 61% |
| Falha mecânica | 161 | 80% |
| Ajuste de qualidade | 122 | 94% |
| Superaquecimento | 48 | 100% |

## Correlações (máquina-dia)

- Temperatura média x horas paradas: r = 0,45
- Vibração média x taxa de defeitos: r = 0,83

## Alertas por máquina

| Máquina | Dias fora do limite (carta) | Horas acima do limite fixo |
| --- | --- | --- |
| M1 | 0 | 0 |
| M2 | 4 | 0 |
| M3 | 41 | 248 |
| M4 | 59 | 183 |
| M5 | 1 | 0 |

## Aviso antecipado: detecção x problema simulado

| Máquina | Problema simulado | Início simulado | 1º sinal (carta) | Limite fixo | Impacto confirmado | Aviso antecipado | Carta x limite fixo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M3 | Aquecimento gradual (ex.: falha de refrigeração), corrigido por manutenção no dia 75 | 10/02 | 14/02 | 02/03 | 09/03 | 23 dias | 16 dias antes |
| M4 | Vibração crescente (ex.: desgaste de rolamento), sem correção até o fim do período | 25/02 | 26/02 | 21/03 | 12/03 | 14 dias | 23 dias antes |

## M3: antes e depois da manutenção

| Período (M3) | Temp. média (°C) | Disponib. | OEE |
| --- | --- | --- | --- |
| referência | 59,6 | 91,7% | 78,9% |
| antes | 74,0 | 81,0% | 69,6% |
| depois | 59,6 | 92,5% | 79,4% |

## M4: situação no fim do período

| Período (M4) | Vibração (mm/s) | Defeitos | OEE |
| --- | --- | --- | --- |
| referência | 1,99 | 1,32% | 80,4% |
| últimos 14 dias | 4,05 | 4,41% | 75,8% |
