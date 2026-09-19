# Evaluación completa de la candidata integrada

**Veredicto: no sustituir H1 por esta candidata.** La combinación empeora el ATT, duplica con creces el KPI de pérdida y aumenta la espera en puertos.

Corrida terminada: 2026-09-14T23:48:45.472194-06:00. Semilla 2026; 140 días de calentamiento y 360 de medición, en 72 intervalos de cinco días. Duración: 24 min 44 s, con observación adicional.

El usuario pidió evaluar la candidata integrada. Se seleccionó IntegratedStrategy solo en el proceso de evaluación, conservando la identidad de UserStrategy en los cuatro módulos del motor. La entrada en disco sigue en H1. Se conservaron antes del avance la clase elegida, MRO, origen de métodos, fuentes y hashes. No se modificó la estrategia competitiva.

## Comparación frente a H1

| Indicador | H1, control conservado | Integrada | Cambio |
| --- | ---: | ---: | ---: |
| ATT medio por intervalo, días | 14.435278 | 15.091667 | +4.55% |
| KPI de pérdida | 11.820352 | 24.579206 | +107.94% |
| TEU medios esperando en puertos | 8,227 | 9,359 | +13.76% |
| TEU medios esperando transbordo | 2,737 | 3,115 | +13.81% |
| TEU medios esperando en origen | 5,491 | 6,244 | +13.71% |
| TEU completados, suma de celdas OD redondeadas | 490,283 | 485,681 | -0.94% |

El ATT aumenta 0.656389 días, equivalentes a 15.75 horas. El KPI es una suma de pérdida relativa ponderada por días, no el ATT ni un porcentaje. Ambos se recalcularon desde las mismas filas redondeadas de los CSV, con idéntico baseline. No se conservó una serie adicional de ATT internos sin redondear.

El control es la salida H1 conservada de la corrida terminada el 13 de septiembre a las 23:43:51, idéntica a las corridas H1 anteriores. No se hizo otra réplica instrumentada de H1. Las nuevas observaciones de máximos no tienen una comparación equivalente en ese control.

## Ventanas críticas

| Días medidos | ATT H1 | ATT integrada | Cambio ATT | KPI H1 | KPI integrada |
| --- | ---: | ---: | ---: | ---: | ---: |
| 41-100 | 13.564 | 13.403 | -0.161 | 0.266 | -0.454 |
| 141-200 | 16.532 | 17.195 | +0.663 | 9.399 | 11.283 |
| 216-240 | 13.714 | 13.722 | +0.008 | -0.693 | -0.679 |
| 261-275 | 13.817 | 14.127 | +0.310 | -0.236 | 0.082 |
| 276-320 | 15.533 | 17.566 | +2.032 | 3.540 | 8.296 |
| 321-330 | 14.460 | 16.100 | +1.640 | 0.032 | 1.044 |
| 331-360 | 14.690 | 17.308 | +2.618 | 0.424 | 4.882 |
| 261-360 (subtotal) | 14.915 | 16.826 | +1.911 | 3.759 | 14.303 |

La ventana 261-360 es un subtotal; no debe sumarse otra vez. Las ventanas describen el conjunto de la red, no el ATT de un único OD.

- Colombo-New Jersey, 41-100, mejora 0.161 días de ATT. Esa ganancia local no compensa las regresiones posteriores.
- Shanghai-Kaohsiung, 141-200, empeora 0.663 días. El máximo de la candidata llega a 20.25 días en 191-195; ese intervalo empeora 4.98 días frente a H1.
- La recuperación 276-320 empeora 2.032 días; los días 331-360 empeoran 2.618 días. Aproximadamente el 83% del aumento total de pérdida proviene de 261-360.
- También empeoran 216-240, 261-275 y 321-330. No hay una compensación global favorable.

## Puertos, rutas y buques

| Puerto | Espera media H1, TEU | Integrada, TEU | Diferencia |
| --- | ---: | ---: | ---: |
| Shanghai | 1,416 | 1,671 | +255 |
| Singapore | 1,128 | 1,333 | +205 |
| Shenzhen | 946 | 1,125 | +179 |
| Colombo | 569 | 676 | +107 |
| Rotterdam | 376 | 482 | +106 |
| New Jersey | 397 | 491 | +94 |
| Piraeus | 516 | 578 | +62 |
| Busan | 472 | 452 | -20 |
| Tianjin | 153 | 149 | -4 |

El transbordo medio sube de 863 a 1,038 TEU en Shanghai, de 675 a 773 en Singapore y de 420 a 488 en Shenzhen. En Piraeus baja ligeramente de 281 a 277, pero la espera de origen sube de 234 a 301. Por eso su espera total empeora aunque no aumente su componente de transbordo.

Las nueve rutas S1-S9 tienen carga media positiva; la utilización agregada baja de 3.54% a 3.52%. Los TEU completados bajan en 4,602 según la suma de las celdas OD publicadas. Las mayores caídas OD incluyen Jebel Ali-Rotterdam (-220) y Jebel Ali-Tanger Med (-214). Son agregados de toda la medición.

Se observaron S1-ALT-1 y S7-ALT-1 en cada muestra diaria de los días 261-360, sin buques desplegados ni carga. No figuran como servicios operados en el CSV de utilización y no registraron salidas de navegación. Esto exige revisar la efectividad de la activación de alternativas; no demuestra por sí solo que hayan causado la regresión ni que fueran exclusivas de esta candidata.

La auditoría de 361 instantáneas diarias (incluido el inicio de medición) revisó 14,801 observaciones de buques: cero anomalías en exclusividad de estado, registro de ruta, capacidad y referencias de carga. Se conservaron las mismas 41 identidades de buques y los mismos legs. Al final no hay reasignaciones pendientes. Los estados no se auditaron continuamente ni se hizo una auditoría completa de todos los bookings y la conservación de TEU.

## Colas observadas y límites de la telemetría

- Máximo total **muestreado diariamente**: 18,350 TEU en el día 286.
- Cola total final, leída de los contadores del modelo: 12,657 TEU.
- Máximos por puerto registrados después de cada actualización de sus contadores: Shanghai 4,816 TEU; Singapore 3,846; Shenzhen 3,493. No se deben sumar máximos ocurridos en horas distintas.
- No hay máximos equivalentes del control H1; no se declara que estos sean un incremento respecto a sus máximos.
- El campo bruto de edad de shipments en la lista de almacenamiento **no es válido para edad de carga pendiente**: esa lista conserva shipments completados y el observador inicial no los excluía. Se preserva el dato bruto, pero se excluye de las conclusiones. Los TEU y máximos anteriores proceden de contadores independientes y no tienen ese problema.

Después de terminar la corrida se corrigió únicamente el filtro de edad del lanzador para futuras observaciones. La copia de inicio en sources_before_run conserva exactamente el código ejecutado; no se volvió a simular ni se sustituyó su evidencia.

## Evaluación y próximos experimentos

Las 95 pruebas unitarias pasadas y la comprobación de enlaces del lanzador respaldan los contratos y la selección de clase; no garantizan mejora competitiva. La corrida completa registra cero errores internos de la estrategia y cero cambios de archivos fuera de su carpeta durante la ejecución. El deterioro observado es suficiente para rechazar esta combinación como sustituto de H1.

No se puede identificar cuál de los mecanismos causó el deterioro con esta combinación. Tampoco hay una réplica H1 con observación idéntica ni una traza de componentes de coste de cada decisión. La observación no programa eventos ni consume números aleatorios; aun así, una futura comparación que requiera atribución más fuerte debe repetir el control con el mismo lanzador.

Próximos pasos recomendados, sin ejecutarlos en esta entrega:

1. Mantener H1 activa y conservar esta candidata y su resultado como experimento rechazado.
2. Separar en nuevas variantes la valoración completa de conexiones y la navegación lenta frente al desvío, usando H1 como control explícito. La H2 aislada ya existente usa el control anterior a H1 y no debe confundirse con una variante H1 más conexiones.
3. Instrumentar los costes realmente comparados al replanificar y las esperas reales de conexión, sobre todo en 191-195 y 276-360. Revisar por qué las alternativas de Piraeus se registran pero no despliegan buques.
4. No ajustar simultáneamente los umbrales de conexiones, atraque o flota. Una mejora de fórmula local necesita validación de la red y de su recuperación.

## Evidencia conservada

- run.json: autorización, selección real, fuentes de inicio, configuración, duración y finalización.
- before_hashes.json / after_hashes.json y historical_checks_before.json / historical_checks_after.json: integridad antes y después.
- Output/: ocho CSV de la candidata; H1_control_Output/: ocho CSV del control usado.
- SimulationProgressResults.log: log completo.
- sources_before_run/: estrategia, entrada, bases, helpers, lanzador y configuración capturados antes de avanzar.
- comparison.json / interval_comparison.csv / analyze.py: comparación reproducible de todos los intervalos, ventanas, puertos, rutas y matrices OD.
- daily_observations.jsonl / state_day_360.json / observation_summary.json / alternative_route_audit.json: observaciones y auditorías adicionales.

El baseline, Input, configuración, escenario, motor, entrada H1 y controles históricos conservan sus hashes. No se realizaron operaciones Git de escritura. No se ejecutó otra hipótesis tras esta candidata.
