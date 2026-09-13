# Round 2: coste a bordo, conexiones y recuperacion

Fecha: 2026-09-13. Analisis original de codigo y CSV del control; no se ejecuto
la simulacion para elaborarlo. Las secciones siguientes conservan ese estado
previo a la corrida observada posteriormente.

Actualizacion de continuidad: la corrida terminada a las 12:01:19 ya esta
archivada en
[RESUMEN.md](benchmark_results/onboard_cost_20260913/observed_run_20260913_120119/RESUMEN.md).
Tiene KPI de perdida 11.8203520321 y ATT medio por intervalo 14.4352777778
dias; es consistente con H1, aunque el log no registra el hash de inicio.
Las menciones a `Output/`, a H1 pendiente de medir y a `candidate_kpi: null`
en el analisis original describen el momento anterior a esa corrida.
Los CSV del control estan preservados en `benchmark_results/onboard_cost_20260913/control/Output/`.
El validador conserva ese manifiesto anterior y ahora rechazara los siete
CSV nuevos de `Output/`; ver los pasos de adaptacion en `../AGENTS.md`
antes de reutilizarlo. No sobrescribir el manifiesto ni los logs historicos.

## Evidencia Local

Los enlaces copiados del otro equipo se corresponden aqui con `Output/` y
`response_strategies/resilience_strategy.py`. Los CSV actuales tienen 72
intervalos de cinco dias, hasta el dia de medicion 360.

El KPI de perdida usado por `validate_resilience.py` es:

```text
L = sum((1 - ATT_baseline_periodo / ATT_escenario_periodo) * dias_periodo)
```

Un aporte negativo representa un periodo mejor que el baseline. Este KPI
no es el ATT medio ni un porcentaje: se calcula sumando la perdida relativa
por la duracion de cada intervalo.

| Dias medidos | Control actual | Referencia anterior |
| --- | ---: | ---: |
| 141-200 | 11.519402 | 17.026701 |
| 261-360 | 8.097363 | 7.204440 |
| Resto | -0.587927 | 3.634514 |
| Total | 19.028839 | 27.865655 |

Fuentes: `Output/ATT_By_Statistics_Interval.csv` y su baseline; referencia
anterior: `benchmark_results/01_expected_time_booking/` con ambos CSV.
El ATT medio de los 72 intervalos actuales es 14.801806 dias.

Control inalterado guardado en `benchmark_results/onboard_cost_20260913/control/`:
`resilience_strategy.py`, `user_strategy.py`, pruebas originales, ocho CSV en
`Output/` y manifiesto SHA-256 de archivos protegidos. Hash SHA-256 de la
estrategia original:

```text
a387c563fb91e77b7f5010e4a3f3b43ca772f4e4d58c80ab5c7be3f5245d502b
```

La carpeta antigua `resilience_20260910_094223/` termina en el dia 325 y marca
`complete: false`. Los valores del control provienen de los CSV completos de
`Output/`; no se presenta ese registro parcial como evidencia de corrida completa.
No se volvio a ejecutar el control para verificar la procedencia de los CSV.

## H1 Implementada: Coste Del Booking Embarcado

`_remaining_cost` excluia los segmentos ya recorridos, pero llamaba a
`_edge_cost(..., transfer=False)`, que igualmente sumaba `headway / 2`.
Esa espera representa esperar otro servicio; no corresponde al booking en
curso a bordo del buque.

Se agrego el argumento privado `onboard=False` a `_edge_cost`. Solamente
`_remaining_cost` lo activa para el booking actual. La diferencia es:

```text
Antes:   distancia_pendiente / velocidad + headway / 2 + espera_puerto
Ahora:   distancia_pendiente / velocidad               + espera_puerto
```

Se conserva la espera por atraque porque el hook ocurre al llegar al puerto,
antes de cargar y descargar. Los bookings futuros mantienen media separacion,
regla de conexiones, penalizacion por ocupacion y coste fijo de transbordo.
El booking actual ya terminado aporta cero y el siguiente sigue siendo una
conexion. El ciclo de tres segmentos de S4 conserva sus indices circulares.

Ejemplo cubierto por prueba: seguir a bordo cuesta 64 h; el calculo anterior
sumaba 48 h ficticias y lo valoraba en 112 h. Una alternativa de 64 h podia
superar el umbral de mejora de 12 h y provocar un transbordo sin ganancia.
H1 conserva el booking en ese caso y permite un transbordo que cuesta 39 h.

La busqueda de caminos para asignacion inicial y candidatos alternativos
conserva su coste existente. Ajustar tambien el primer edge candidato cuando
continua en el mismo buque requeriria revisar la busqueda y su cache; no
forma parte de este experimento sobre el coste pendiente del plan actual.

## H2 Analizada: Rechazo De Conexiones

`_edge_cost` rechaza una conexion cuando:

```text
headway / 2 < CONNECTION_BUFFER * espera_puerto
```

Con espera de 8 h y buffer de 1.5, un servicio cada 12 h se rechaza
(6 < 12), mientras uno cada 48 h se admite (24 >= 12). La frecuencia no
informa la hora de llegada del buque ni la holgura real de una conexion.

Proximo experimento propuesto: sustituir ese veto por una penalizacion finita
de riesgo para conexiones operativas. Mantener imposibilidad cuando no haya
flota utilizable o el puerto este cerrado. La forma y escala de la penalizacion
deben fijarse antes de la corrida y evaluarse como H2, sin retocar otros umbrales.

Ademas, en `adjust_bookings_before_cargo_handling`, la primera conexion a otra
ruta solo usa el coste de transferencia para comprobar que sea finito; luego
suma 18 h al coste calculado como origen. La penalizacion por rho de esa primera
conexion no se incorpora al valor comparado. H2 deberia usar el coste completo
consistentemente en la comparacion y en la seleccion del candidato, evitando
sumar dos veces la espera por puerto o por servicio. Esto sigue pendiente.

## H3 Analizada: Navegacion Lenta Frente A Desvio

Actualmente hay dos exclusiones coherentes entre si:

- `_snapshot` pasa los legs congestionados a `_build_all_candidate_bookings`,
  que descarta bookings que los atraviesen.
- `_remaining_cost` devuelve infinito si algun leg pendiente tiene
  `sailing_time_multiplier > 1`.

Asi no se compara el tiempo de cruzar un leg lento con el de un desvio con
varios transbordos. El headway si incorpora el multiplicador, pero
`edge.total_distance / speed` usa distancia sin ponderar.

Para un experimento H3 habria que permitir esos legs y sumar por segmento
`sailing_distance * sailing_time_multiplier / speed` tanto en caminos nuevos
como en el plan pendiente. Mantener separados los cierres de puerto y no
suponer que un tramo con multiplicador 5 esta cerrado.

No basta con pasar una coleccion vacia de legs congestionados al constructor:
este tambien usa esa coleccion para obtener la clave de disrupcion y decidir
si una ruta alternativa es reservable. Una implementacion futura dentro de
strategies debe conservar la clave activa correcta. No modificar el motor.

## Recuperacion Y Ventanas De Evaluacion

Disrupciones de `scenario_builders/disruption_scenario.py`, relativas a la
medicion: Colombo-New Jersey 40-99; Shanghai-Kaohsiung 140-199;
Qingdao-Busan 215-239; cierre de Piraeus 260-273; cierre de Tianjin 320-326.
La configuracion conserva warm-up 140, medicion 360 e intervalos de cinco dias.

Las ventanas siguientes agrupan intervalos CSV completos. Sus bordes no
coinciden exactamente con todos los inicios y finales de disrupcion.

| Ventana CSV | Aporte del control al KPI |
| --- | ---: |
| 41-100 | -0.325868 |
| 141-200 | 11.519402 |
| 216-240 | -0.834392 |
| 261-275 | 0.037967 |
| 276-320 | 6.454586 |
| 321-330 | 0.245437 |
| 331-360 | 1.359374 |

Un 79.7% de la perdida de los ultimos 100 dias cae en 276-320, despues del
cierre de Piraeus. Esto justifica revisar recuperacion y transbordos, pero no
demuestra que el error de headway sea la causa de ese deterioro.

El CSV agregado de puertos muestra 8,626 TEU de espera total: Shanghai 1,839,
Singapore 1,194, Shenzhen 765, Colombo 624 y Busan 494. Piraeus registra 469 y
Tianjin 155. Son estadisticas agregadas, no colas medidas especificamente en
261-360 ni maximos de acumulacion. El CSV de rutas presenta solo S1-S9, con
utilizacion total 3.55%; los estados medios suman 41 buques (38.82 navegando,
0.19 esperando atraque y 1.99 atendidos).

La restauracion de buques desde rutas alternativas exige buque vacio y un
puerto compatible con la ruta original. Esto puede prolongar la recuperacion
si quedara carga a bordo. Los CSV disponibles no registran decisiones de
rebooking ni permiten atribuir la perdida temporal a esa restauracion.

Tras autorizacion para simular H1: conservar primero las salidas anteriores,
ejecutar con semilla 2026 y configuracion intacta, archivar los ocho CSV y la
variante exacta. Comparar KPI total, ATT medio, todas las ventanas anteriores,
espera por puerto, utilizacion y estados. H2 y H3 deben ser variantes separadas;
si se comparan de forma acumulativa, declarar que control se usa en cada caso.

## Verificacion Sin Simulacion

```powershell
.\.venv\Scripts\python.exe -B response_strategies/validate_onboard_cost.py
```

Ejecuta pruebas unitarias estaticas y de contratos, bloquea `Model.run` y
`Model.warmup`, y excluye expresamente la prueba que avanza diez dias.
Comprueba el manifiesto protegido antes y despues y escribe `unit_tests.log`
y `validation.json` dentro de `benchmark_results/onboard_cost_20260913/`.
`candidate_kpi: null` significa que la candidata no se ha simulado.

Resultado final: 25 pruebas pasaron, una prueba con avance de simulacion fue
excluida; cero llamadas a `Model.run` y `Model.warmup`; los 163 archivos
protegidos conservaron sus hashes. Las pruebas cubren el coste pendiente,
bookings futuros, indices circulares de S4, falsa ganancia de transbordo,
alternativas utiles, prefijo completado y referencias inversas.

No ejecutar `validate_resilience.py --tests-only` bajo la restriccion actual:
ese conjunto incluye avance de simulacion. Los fallos historicos del calculador
faltante y de `DASHBOARD_URL` no se corrigen ni se reevaluan aqui.

La primera ejecucion unitaria encontro dos casos con un puerto destino sin
metricas en la fixture nueva (23 pruebas pasaron). Se completo esa fixture;
el log inicial se conserva separado como `unit_tests_initial_fixture_failure.log`.
No fue un fallo preexistente del motor ni un resultado de simulacion.
