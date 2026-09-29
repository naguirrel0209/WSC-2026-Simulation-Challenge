# AGENTS.md

Guia para agentes que trabajen en Round 2 del WSC 2026 Simulation Challenge.

## Regla Central

```text
Todo cambio competitivo debe estar dentro de response_strategies/
```

No modificar archivos fuera de esa carpeta salvo solicitud explicita del
usuario. Los archivos `README.md` y `AGENTS.md` de la raiz existen por solicitud
expresa y documentan el proyecto; no forman parte de la estrategia ejecutable.

## Estado Actual Y Pasos Para La Proxima Ronda (2026-09-29)

Esta seccion refleja la entrega final de Round 2 y prevalece sobre las
referencias historicas a H1 y E1 que aparecen mas abajo. La entrada activa es
`response_strategies/user_strategy.py`; su implementacion esta en
`response_strategies/round2_strategy.py`. La corrida completa archivada en
`response_strategies/benchmark_results/round2_optimized_strategy_run_20260923_172158/`
reporta ATT medio de 13.9504166667 dias y Loss de 0.614422312139. La limpieza
de comentarios de esta entrega no cambia la estructura ejecutable; no se ha
realizado una nueva simulacion tras esa limpieza.

1. Conservar el commit de esta entrega, ambos archivos de estrategia y la
   corrida archivada como referencia reproducible. Registrar los hashes de los
   archivos activos antes de iniciar cualquier adaptacion.
2. Al recibir el material oficial de la proxima ronda, leer sus reglas,
   contratos, archivos de entrada, escenario, KPI y permisos de modificacion.
   No asumir que las rutas, indices, ventanas, semilla o configuracion de Round 2
   continuan iguales.
3. Inspeccionar la nueva red y construir un control sin estrategia personalizada
   con los parametros oficiales, solo cuando el usuario autorice la simulacion.
   Guardar codigo, configuracion, semilla, log, CSV y hashes antes de comparar.
4. Adaptar la estrategia dentro del directorio permitido por las nuevas reglas.
   Verificar importacion, contratos, conectividad de rutas, reservas, indices y
   conservacion de buques con pruebas que no ejecuten la simulacion.
5. Formular una hipotesis medible por variante. Congelar codigo y manifiesto
   antes de cada corrida autorizada; archivar la salida completa y comparar
   ATT, KPI, ventanas criticas, colas, transbordos, utilizacion y estados de
   buques con el control de esa ronda.
6. Promover una variante solo si mejora el objetivo oficial sin violar las
   restricciones ni provocar acumulaciones o estados inconsistentes. Documentar
   tambien las regresiones locales y conservar las variantes rechazadas.

Hasta que el usuario indique lo contrario, sigue vigente la prohibicion de
simular. La autorizacion de commit y push de esta entrega no se extiende a
cambios o corridas posteriores.

## Limites De Trabajo

1. No cambiar `Input/`, `config/`, `scenario_builders/`, `simulation_model/` ni
   `maritime_data_context/` para mejorar el resultado.
2. No cambiar la semilla `2026`, warm-up, duracion ni intervalos entre pruebas.
3. Leer `response_strategies/user_strategy.py` y
   `response_strategies/strategy_validation.py` antes de editar.
4. Mantener scripts, variantes y resultados comparativos dentro de
   `response_strategies/`.
5. Implementar una hipotesis medible por experimento y conservar su salida
   antes de ejecutar la siguiente.
6. No copiar estrategias de Round 1 sin adaptar rutas, indices y ventanas.

## Restricciones Vigentes Del Usuario (2026-09-13)

- No ejecutar la simulacion, ni siquiera como parte de una prueba corta.
- El usuario autorizo expresamente un commit local de los cambios realizados
  y esta actualizacion de `AGENTS.md` el 2026-09-13. Esa solicitud sustituye
  la prohibicion anterior de commit para esta entrega. No autoriza push,
  pull, merge ni nuevas simulaciones; futuras escrituras Git requieren
  autorizacion en la tarea correspondiente.
- Modificar codigo, pruebas, analisis y artefactos solo en `response_strategies/`.
  La actualizacion de este `AGENTS.md` en la raiz esta autorizada expresamente.
- Implementar una sola hipotesis a la vez. La candidata actual aplica solo H1:
  retirar la media separacion entre servicios del coste del booking ya embarcado.
- H2 (penalizacion de conexiones) y H3 (navegacion lenta frente a desvio) siguen
  pendientes de experimentos separados. No activarlas junto con H1.
- No cambiar umbrales de atraque, ocupacion, conexiones, congestion o flota.
- El protocolo de corrida y los comandos generales de abajo solo se aplican
  cuando el usuario autorice expresamente una simulacion en una tarea posterior.

## Entrega Actual Y Continuidad

- Entrada activa: `response_strategies/user_strategy.py`, que hereda de
  `response_strategies/resilience_strategy.py`.
- Leer `response_strategies/ONBOARD_COST_ANALYSIS.md` y
  `response_strategies/benchmark_results/onboard_cost_20260913/observed_run_20260913_120119/RESUMEN.md`
  antes de continuar. El primero conserva el analisis previo; el segundo
  documenta la corrida completa observada posteriormente.
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
- La ultima verificacion unitaria guardada sigue siendo 25 pruebas pasadas,
  una excluida; cero llamadas a `Model.run` o `Model.warmup`. Su
  `validation.json` precede a la corrida; `candidate_kpi: null` es historico.
  El KPI observado posterior esta en el `metrics.json` de la corrida archivada.
- `validate_onboard_cost.py` bloquea `Model.run` y `Model.warmup`, excluye
  la prueba de diez dias y usa `-B` y pytest sin cache. Sin embargo, compara
  contra el manifiesto anterior, que incluye los CSV de `Output/`, y ahora
  rechazara esa diferencia antes de ejecutar pruebas. Antes de reutilizarlo,
  adaptar la verificacion como se indica abajo; no sobrescribir el control
  ni los resultados unitarios historicos para hacer pasar el chequeo.
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
2. Antes de nuevas pruebas, adaptar el validador dentro de `response_strategies/`
   para verificar entradas, configuracion, escenario, motor y baseline contra
   el control original; comprobar los CSV actuales contra la corrida archivada
   y registrar por separado cambios documentales autorizados. Congelar un
   manifiesto nuevo para comparar antes/despues de las pruebas y guardar
   resultados en una carpeta nueva. Mantener los bloqueos de avance del
   modelo y la exclusion de la prueba de diez dias. No actualizar hashes de
   entradas o motor para ocultar diferencias y no modificar el control.
3. Revisar primero las regresiones de espera/transbordo en Shenzhen y Piraeus
   y las ventanas de Colombo-New Jersey y Qingdao-Busan usando los archivos
   guardados. Los maximos de cola y los estados individuales de buques siguen
   pendientes de observacion en una futura corrida autorizada.
4. En la proxima corrida autorizada, guardar ANTES de iniciar el hash y la
   copia de la variante exacta, entrada, manifiesto protegido, semilla y
   configuracion. Si se requiere confirmar la atribucion de H1, repetir H1
   sin ajustes. Registrar el log y los ocho CSV al terminar. Ninguna de estas
   corridas esta autorizada por la solicitud de commit.
5. La siguiente hipotesis propuesta es H2: sustituir el veto de conexiones
   operativas por una penalizacion finita y usar consistentemente el coste
   completo de transferencia. Definir su formula y prueba medible antes de
   implementar, conservar imposibilidad por cierre o falta de flota y no
   retocar otros umbrales. Prepararla en una variante separada desde el
   control previo a H1, con H1 desactivada; mantener H1 activa hasta la tarea
   correspondiente. No activar H1+H2 sin una instruccion posterior que
   autorice expresamente un experimento acumulativo y defina su control.
6. Evaluar H3 despues, en otro experimento aislado: comparar el tiempo de
   navegar por legs lentos con el desvio, ponderando la distancia de cada
   segmento por su multiplicador. Conservar cierres, conectividad, indices
   circulares de S4 y la clave de disrupcion de las rutas alternativas.
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

## Comandos

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe dashboard\serve_gui.py --no-open
```
