# Resumen de corrida Round 2 optimizada

La simulacion termino el 2026-09-23 y escribio resultados en `Output/`.
Se ejecuto desde la raiz del monorepo usando `SimulationChallenge2026_Py_Round2/main.py`.

## Resultado

- Log: `202609231653_SimulationProgressResults.log`
- Duracion reportada: `00:28:39`
- Dias medidos: 360, con warm-up de 140 dias
- Loss: `0.614422312139`
- ATT medio: `13.9504166667` dias
- Baseline medio: `13.8541111111` dias
- TEU promedio en espera: `7,859`
- Utilizacion total de rutas: `3.54%`

## Ventanas principales

| Ventana | ATT | Baseline | Loss |
| --- | ---: | ---: | ---: |
| 41-100 Colombo-New Jersey | 13.136667 | 13.497833 | -1.673268 |
| 141-200 Shanghai-Kaohsiung | 13.594167 | 13.793000 | -0.897724 |
| 216-240 Qingdao-Busan | 13.796000 | 14.092000 | -0.543629 |
| 261-275 Piraeus closure | 13.710000 | 14.017333 | -0.368760 |
| 276-320 post-Piraeus | 16.582222 | 14.255333 | 6.037480 |
| 321-330 Tianjin closure | 14.630000 | 14.413000 | 0.146048 |
| 331-360 post-Tianjin | 14.745000 | 14.467000 | 0.559916 |

La ventana 276-320 sigue siendo el mayor aporte de perdida. El total queda
cerca del baseline gracias a mejoras en las ventanas de las primeras
disrupciones.
