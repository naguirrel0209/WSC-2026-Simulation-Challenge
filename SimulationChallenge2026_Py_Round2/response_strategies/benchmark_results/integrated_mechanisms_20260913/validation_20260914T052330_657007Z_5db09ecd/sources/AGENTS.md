# AGENTS.md

Guia para agentes que trabajen en Round 2 del WSC 2026 Simulation Challenge.

## Regla Central

```text
Todo cambio competitivo debe estar dentro de response_strategies/
```

No modificar archivos fuera de esa carpeta salvo solicitud explicita del
usuario. Los archivos `README.md` y `AGENTS.md` de la raiz existen por solicitud
expresa y documentan el proyecto; no forman parte de la estrategia ejecutable.

## Limites De Trabajo

1. No cambiar `Input/`, `config/`, `scenario_builders/`, `simulation_model/` ni
   `maritime_data_context/` para mejorar el resultado.
2. No cambiar la semilla `2026`, warm-up, duracion ni intervalos entre pruebas.
3. Leer `response_strategies/user_strategy.py` y
   `response_strategies/strategy_validation.py` antes de editar.
4. Mantener scripts, variantes y resultados comparativos dentro de
   `response_strategies/`.
5. Definir hipotesis y control por experimento y conservar su salida antes
   del siguiente. Para atribucion individual, aislar cada hipotesis. La
   candidata conjunta autorizada abajo se evalua como una combinacion.
6. No copiar estrategias de Round 1 sin adaptar rutas, indices y ventanas.

## Restricciones Vigentes Del Usuario (2026-09-13)

- No ejecutar la simulacion, ni siquiera como parte de una prueba corta.
  El usuario reitero esta prohibicion al solicitar actualizar este archivo.
- Git exclusivamente para lectura: status, diff, log y show. No add, commit,
  merge, push, pull, fetch, rebase, reset, checkout, switch, stash ni clean.
  La autorizacion de commit de una entrega anterior es historica y no
  autoriza escrituras Git en esta tarea.
- Modificar codigo, pruebas, analisis y artefactos solo en `response_strategies/`.
  La actualizacion de este `AGENTS.md` en la raiz esta autorizada expresamente.
- Mantener H1 como entrada activa: retirar la media separacion entre servicios
  del coste del booking ya embarcado. No sustituir `user_strategy.py`.
- El usuario solicito agregar los tres mecanismos: conexiones operativas con
  penalizacion finita, coste completo de transbordo y comparacion entre
  navegacion lenta y desvio. Se implemento una candidata separada H1+H2+H3.
  Esta solicitud permite preparar la combinacion; no autoriza simularla ni
  activarla. Su control futuro es H1 y no permite atribucion individual.
- Conservar tambien H2 aislada, cuyo control es anterior a H1. No sobrescribir
  variantes ni evidencias historicas. H2 y H3 siguen sin KPI medido.
- No cambiar umbrales de atraque, ocupacion, conexiones, congestion o flota.
- El protocolo de corrida y los comandos generales de abajo solo se aplican
  cuando el usuario autorice expresamente una simulacion en una tarea posterior.

## Entrega Actual Y Continuidad

- Entrada activa: `response_strategies/user_strategy.py`, que hereda de
  `response_strategies/resilience_strategy.py`. Sigue siendo H1.
- Candidata conjunta: `response_strategies/integrated_strategy.py`, clase
  `IntegratedStrategy`. Implementa H1+H2+H3; permanece sin activar.
  Conserva coste de transferencia completo, coste por segmento ponderado
  y la clave real de disrupcion de rutas alternativas. La continuacion a
  bordo no suma espera de otro servicio, tanto en el plan como en la candidata.
- H2 aislada: `response_strategies/h2_connection_strategy.py`, basada en la
  copia exacta `h2_control_strategy.py` del control previo a H1. No contiene
  H1 ni H3. Las dos candidatas conservan umbrales de atraque/conexion/flota.
- Leer `response_strategies/ONBOARD_COST_ANALYSIS.md` y
  `response_strategies/benchmark_results/onboard_cost_20260913/observed_run_20260913_120119/RESUMEN.md`
  antes de continuar. El primero conserva el analisis previo; el segundo
  documenta la corrida completa observada posteriormente.
- Leer tambien `response_strategies/INTEGRATED_MECHANISMS.md`,
  `response_strategies/INTEGRATED_VALIDATION.md`,
  `response_strategies/H2_HYPOTHESIS.md` y `response_strategies/H2_DIAGNOSIS.md`.
- Control conservado: `response_strategies/benchmark_results/onboard_cost_20260913/control/`.
  Contiene estrategia original, entrada, pruebas originales, los ocho CSV de
  `Output/` y `protected_hashes.json` (SHA-256 de 163 archivos protegidos).
- El control tiene KPI de perdida 19.0288385840 y ATT medio por intervalo
  14.8018055556 dias. **19.03 no es el ATT medio.**
- La referencia anterior de KPI 27.8656551610 esta en
  `response_strategies/benchmark_results/01_expected_time_booking/`.
- `resilience_20260910_094223/` contiene solo 325 dias y `complete: false`;
  no usar esa carpeta como corrida completa. El control copia los 360 dias
  presentes en `Output/` sin volver a simular.
- Corrida observada: termino el 2026-09-13 a las 12:01:19, con 140 dias de
  warm-up y 360 dias medidos en 72 intervalos; duracion real 00:15:02.
  Esta archivada en
  `response_strategies/benchmark_results/onboard_cost_20260913/observed_run_20260913_120119/`:
  ocho CSV, log completo, estrategia y entrada capturadas despues de la corrida,
  `snapshot_hashes.json`, `metrics.json` y `RESUMEN.md`.
- La ultima corrida disponible termino a las 18:53:53 del 2026-09-13:
  `Logs/202609131838_SimulationProgressResults.log`, duracion 00:15:04,
  140 dias de warm-up y 360 medidos. Los ocho CSV actuales son identicos
  por SHA-256 a los de la corrida de las 12:01:19. No hubo mejora adicional.
  La entrada actual sigue en H1; esos resultados no miden las candidatas.
- Resultados observados: KPI de perdida **11.8203520321** (-37.88% frente al
  control), ATT medio por intervalo **14.4352777778 dias** (-2.48%; -8.80 h).
  El baseline medio es 13.8541111111 dias. El ATT se recalcula desde las filas
  redondeadas del CSV; su fila `OverallMean` muestra 14.43 usando valores
  internos sin redondear. **11.82 es el KPI de perdida, no el ATT.**
- La estrategia activa coincide con H1 y con el hash validado
  `bde16bfcd00ab5084beded9e99baa7a1d393b329306797be8211165daa2fac1b`.
  Su modificacion precede al inicio del log, pero el log no registra el hash
  cargado al iniciar. Describir la corrida como consistente con H1 y la mejora
  como observada; no afirmar una atribucion exacta o una replica independiente.
- La espera media en puertos baja de 8,626 a 8,227 TEU; la de transbordo,
  de 2,983 a 2,737. Vigilar Shenzhen (765 -> 946 TEU) y Piraeus (469 -> 516).
  Los CSV son promedios, no maximos ni colas finales. Utilizacion total 3.54%;
  total medio reportado de buques 41.00. No permiten auditar estados finales
  individuales ni descartar rutas alternativas temporales sin carga.
- Al resumir la corrida, 156 de los 163 hashes del control seguian intactos:
  solo cambiaron los siete CSV generados de `Output/`. Entradas, configuracion,
  escenario, motor y baseline no cambiaron. Este es un registro historico;
  las actualizaciones documentales posteriores deben identificarse aparte.
- La verificacion historica original de H1 conserva 25 pruebas pasadas,
  una excluida; cero llamadas a `Model.run` o `Model.warmup`. Su
  `validation.json` precede a la corrida; `candidate_kpi: null` es historico.
  El KPI observado posterior esta en el `metrics.json` de la corrida archivada.
- La primera validacion de la candidata conjunta paso 90 pruebas, excluyo
  una y tuvo cero llamadas a Model.run/Model.warmup y entradas de avance
  de Sandbox. No cambio ningun archivo vigilado durante las pruebas.
  El registro es `response_strategies/benchmark_results/integrated_mechanisms_20260913/validation_20260914T051823_729270Z_ee57fdbe/`.
  Las verificaciones posteriores de esta actualizacion documental se
  identifican en `response_strategies/INTEGRATED_VALIDATION.md`.
- Los validadores ya separan las protecciones: 156 archivos contra el control
  original (incluido baseline), ocho CSV archivados del control, once elementos
  del snapshot observado y ocho CSV actuales contra ese snapshot. Conservan
  hashes fijos de los manifiestos historicos y registran aparte cambios
  documentales autorizados. Cada ejecucion crea una carpeta nueva con
  copias de fuentes, hashes antes/despues y resultados.
- Usar `validate_integrated.py` para la candidata conjunta y la suite previa;
  `validate_onboard_cost.py` conserva la suite de H1/H2/integridad. Ambos
  delegan en `validate_connections.py`, usan -B y pytest sin cache/plugins
  automaticos, y bloquean Model.run/Model.warmup y diez entradas de Sandbox.
  La prueba de diez dias se excluye explicitamente por nombre completo.
- No usar `validate_resilience.py --tests-only` ni `pytest` sin seleccion bajo
  la restriccion actual: algunas pruebas ejecutan la simulacion.
- Las ventanas 141-200 y 261-360 bajan de 11.5194 a 9.3992 y de 8.0974
  a 3.7590 puntos de perdida. En 276-320 el aporte baja de 6.4546 a 3.5398.
  Colombo-New Jersey (41-100) y Qingdao-Busan (216-240) empeoran ligeramente.
  Consultar todas las ventanas y los retrocesos locales antes de aceptar
  una variante; un mejor total no basta.

## Pasos A Seguir

1. Mantener H1 como entrada activa y conservar inalterados el control y la
   corrida observada. La regla `.gitattributes` dentro del archivo de resultados
   conserva los bytes de las copias para que Git no normalice sus finales de
   linea y rompa los hashes. No confundir una copia posterior del codigo con
   un registro de la estrategia cargada al iniciar.
2. Usar los validadores seguros indicados arriba. Si hay diferencias de
   integridad, investigarlas; no refrescar hashes de entradas, motor, baseline
   o controles para ocultarlas. La actualizacion autorizada de AGENTS.md se
   registra en `response_strategies/authorized_documentation_changes.json`.
   Ese registro no permite excepciones para codigo, datos ni configuracion.
3. Revisar primero las regresiones de espera/transbordo en Shenzhen y Piraeus
   y las ventanas de Colombo-New Jersey y Qingdao-Busan usando los archivos
   guardados. Los maximos de cola y los estados individuales de buques siguen
   pendientes de observacion en una futura corrida autorizada.
4. En la proxima corrida autorizada, guardar ANTES de iniciar el hash y la
   copia de la variante exacta, entrada, manifiesto protegido, semilla y
   configuracion. Si se requiere confirmar la atribucion de H1, repetir H1
   sin ajustes. Registrar el log y los ocho CSV al terminar. Ninguna de estas
   corridas esta autorizada por la solicitud actual de codigo o documentacion.
5. Las formulas de H2 y de la candidata conjunta ya estan documentadas.
   H2 usa penalizacion `max(0, 1.5*espera - headway/2)`, mas ocupacion y
   18 h de transferencia. La conjunta agrega la suma de distancia de cada
   leg multiplicada por su propio multiplicador y conserva H1 a bordo.
   Mantener la H2 aislada y la conjunta en sus archivos separados.
6. Para una futura evaluacion conjunta comparar H1+H2+H3 contra H1, siguiendo
   `INTEGRATED_MECHANISMS.md` y las observaciones del protocolo H2. Para
   aislar H2 usar el control previo a H1; para aislar H3 haria falta preparar
   otra variante/control. No interpretar un resultado conjunto como prueba
   de cada mecanismo por separado. Ninguna corrida nueva esta autorizada.
7. Para cada variante comparar ATT medio, KPI total y ventanas 41-100,
   141-200, 216-240, 261-275, 276-320, 321-330 y 331-360; usar 261-360 solo
   como subtotal. Revisar espera por puerto, transbordos, carga de rutas,
   acumulaciones y estados de los 41 buques. Archivar todo antes de cambiar
   de hipotesis; no declarar una mejora comprobada con una corrida parcial.

## Archivos Relevantes

- Entrada: `main.py`
- Solucion: `response_strategies/user_strategy.py`
- Fallback: `response_strategies/default_strategy.py`
- Validacion: `response_strategies/strategy_validation.py`
- Candidata conjunta: `response_strategies/integrated_strategy.py`
- Pruebas seguras: `response_strategies/validate_integrated.py`
- Diagnostico y continuidad: `response_strategies/INTEGRATED_VALIDATION.md`
- Configuracion: `config/simulation_config.py`
- Disrupciones: `scenario_builders/disruption_scenario.py`
- KPI: `Output/ATT_By_Statistics_Interval.csv`

## Contratos De Estrategia

### `select_vessel_for_berth(...)`

- Solo se llama cuando la cola alcanza el umbral de congestion.
- Debe devolver exactamente un objeto contenido en `waiting_vessels`.
- Una politica puede combinar espera, TEU descargable, capacidad y urgencia.

### `create_alternative_service_routes(...)`

- No puede crear, eliminar ni reemplazar legs o buques.
- Toda ruta nueva debe usar legs existentes y formar un ciclo conectado.
- Un buque transferido debe proceder de una ruta ya existente.
- La validacion se ejecuta despues de cada llamada, incluso si retorna `None`.

### `assign_associated_bookings(...)`

- Debe crear bookings ordenados y conectados desde origen hasta destino.
- Debe registrar cada booking en `shipment.associated_bookings` y en
  `service_route.associated_bookings`.
- Debe definir `shipment.current_booking_index`.
- Debe limpiar referencias inversas de bookings reemplazados.

### `adjust_bookings_before_cargo_handling(...)`

- Es el unico punto para replanificar shipments embarcados.
- Se ejecuta al llegar a puerto y antes de la carga/descarga.
- Debe conservar la parte ya completada y mantener indices consistentes.

Devolver `None` permite usar la estrategia fallback para esa decision.

## Escenario Round 2

Disrupciones, relativas al inicio de medicion:

- `Colombo -> New Jersey`: dias 40-99, multiplicador 5.
- `Shanghai -> Kaohsiung`: dias 140-199, multiplicador 5.
- `Qingdao -> Busan`: dias 215-239, multiplicador 5.
- Cierre de `Piraeus`: dias 260-273.
- Cierre de `Tianjin`: dias 320-326.

La red usa 20 puertos, 9 rutas, 54 segmentos y 41 buques. `S4` tiene solo tres
segmentos: `Shanghai -> Kaohsiung -> Los Angeles -> Shanghai`.

## Protocolo Antes De Cada Corrida

Solo despues de una autorizacion posterior del usuario para simular.

1. Confirmar que solo cambian archivos permitidos en `response_strategies/`.
2. Validar que entradas, configuracion y escenario conservan sus hashes.
3. Ejecutar pruebas rapidas y registrar fallos preexistentes por separado.
4. Verificar que la variante de `user_strategy.py` importa y respeta contratos.
5. Copiar la salida anterior a `response_strategies/benchmark_results/`.
6. Ejecutar la simulacion completa con semilla `2026`.
7. Copiar todos los CSV y la variante probada a una carpeta propia.
8. Comparar ATT medio, periodos criticos, espera por puerto, uso de rutas y
   estados de buques.

## Estado De Referencia

Primera corrida disruptiva sin estrategia personalizada:

- ATT medio: 15.532 dias.
- Baseline medio: 13.854 dias.
- Diferencia: +1.678 dias, o +12.1%.
- Ventana mas critica: dias 146-195, asociada principalmente con
  `Shanghai -> Kaohsiung`.
- Espera total observada: 9,894 TEU.
- Utilizacion media total de rutas: 3.50%.

Esto indica que el principal problema observado es asignacion y tiempo de
respuesta, no falta global de capacidad.

## Fallos Preexistentes De Pruebas

- Falta el modulo `resilience_kpi_calculator` requerido por una prueba.
- Una prueba del dashboard espera `main.DASHBOARD_URL`, constante que ya no
  existe porque Round 2 selecciona el puerto dinamicamente.
- Excluyendo el calculador faltante: 210 pruebas pasan y 1 falla por el punto
  anterior.

No corregir esos fallos dentro de una implementacion competitiva.

## Criterio De Mejora

Una variante mejora solo si reduce el ATT medio con la misma semilla y no crea
acumulaciones extremas de TEU, rutas alternativas sin carga o estados
inconsistentes. No aceptar una mejora global sin revisar los periodos de las
cinco disrupciones y los puertos con mayor espera.

## Comandos Seguros Sin Simulacion

```powershell
.\.venv\Scripts\python.exe -B response_strategies/validate_integrated.py
.\.venv\Scripts\python.exe -B response_strategies/validate_onboard_cost.py
```

## Comandos Generales (No Ejecutar Bajo La Restriccion Actual)

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe dashboard\serve_gui.py --no-open
```
