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
5. Implementar una hipotesis medible por experimento y conservar su salida
   antes de ejecutar la siguiente.
6. No copiar estrategias de Round 1 sin adaptar rutas, indices y ventanas.

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
