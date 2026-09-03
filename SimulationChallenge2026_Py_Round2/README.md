# WSC 2026 Simulation Challenge - Round 2

Este proyecto contiene el codigo Python de la ronda 2 del WSC 2026
Simulation Challenge. Simula una red maritima de contenedores, aplica
disrupciones planificadas y genera archivos CSV para evaluar el desempeno de
las estrategias y visualizarlo en un dashboard local.

## Regla Importante De La Competencia

Las reglas son las mismas que en la ronda 1:

```text
Toda modificacion de la solucion competitiva debe estar dentro de response_strategies/
```

Esto incluye algoritmos, scripts de experimentacion y documentos explicativos
que formen parte de la entrega. No se deben modificar `Input/`, `config/`,
`scenario_builders/`, `simulation_model/` ni `maritime_data_context/` para
obtener una mejora competitiva.

## Estructura Del Proyecto

```text
.
+-- main.py
+-- requirements.txt
+-- simulation_output_csv_writer.py
+-- config/
+-- dashboard/
+-- Input/
+-- maritime_data_context/
+-- o2despy/
+-- Output/
+-- response_strategies/
+-- scenario_builders/
+-- simulation_model/
```

- `main.py`: ejecuta warm-up, simulacion medida, exportacion y dashboard.
- `Input/`: puertos, rutas, tramos, demanda, clases de buques y flota.
- `scenario_builders/`: construye el escenario base y el escenario disruptivo.
- `simulation_model/`: motor de eventos discretos y actividades maritimas.
- `maritime_data_context/`: entidades como `Port`, `Vessel`, `Shipment`,
  `Booking`, `ServiceRoute`, `Leg` y `Demand`.
- `response_strategies/`: unica zona valida para la solucion competitiva.
- `Output/`: CSV generados por la ultima corrida.
- `dashboard/`: interfaz local que consume los CSV de `Output/`.
- `o2despy/`: libreria local usada por el motor.

## Configuracion Actual

- Warm-up: 140 dias.
- Periodo medido: 360 dias.
- Intervalo estadistico: 5 dias.
- Semilla: `2026`.
- Estrategias habilitadas: `ENABLE_STRATEGY = True`.
- Escenario predeterminado: `scenario_builders.create_with_disruption()`.

Los dias de disrupcion se expresan respecto del inicio del periodo medido. El
constructor agrega internamente los 140 dias de warm-up.

### Disrupciones De Round 2

Tramos congestionados:

- `Colombo -> New Jersey`: dia 40, duracion 60 dias, multiplicador 5.
- `Shanghai -> Kaohsiung`: dia 140, duracion 60 dias, multiplicador 5.
- `Qingdao -> Busan`: dia 215, duracion 25 dias, multiplicador 5.

Puertos cerrados:

- `Piraeus`: dia 260, duracion 14 dias.
- `Tianjin`: dia 320, duracion 7 dias.

## Como Ejecutar

Desde PowerShell, en la raiz de Round 2:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Si PowerShell bloquea la activacion:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Al terminar se escriben los CSV en `Output/`. El dashboard usa el primer
puerto disponible a partir de `8000`.

Para lanzar solo el dashboard:

```powershell
python dashboard\serve_gui.py
python dashboard\serve_gui.py --no-open
```

## Donde Implementar La Solucion

El archivo principal de la solucion es:

```text
response_strategies/user_strategy.py
```

Contiene cuatro puntos de decision:

1. `select_vessel_for_berth(...)`: selecciona un buque de la cola cuando el
   puerto alcanza el umbral de congestion.
2. `create_alternative_service_routes(...)`: crea rutas ciclicas usando solo
   legs y buques existentes.
3. `assign_associated_bookings(...)`: crea la cadena inicial de bookings de un
   shipment.
4. `adjust_bookings_before_cargo_handling(...)`: replanifica carga embarcada al
   llegar a puerto y antes de carga/descarga.

Cuando una funcion devuelve `None`, el modelo usa la implementacion de
`response_strategies/default_strategy.py`.

### Restricciones Criticas

- No crear ni eliminar buques.
- No crear ni eliminar legs.
- Toda ruta nueva debe ser un ciclo conectado y usar legs existentes.
- El buque de una ruta nueva debe provenir de una ruta preexistente.
- Toda reserva debe registrarse tanto en el shipment como en la ruta.
- Al reemplazar reservas se deben limpiar referencias inversas obsoletas.
- `shipment.current_booking_index` debe permanecer consistente.

## KPI Y Comparacion

El KPI principal es `AverageTransportTime`, ponderado por TEU:

```text
Output/ATT_By_Statistics_Interval.csv
```

Cada experimento debe usar la misma semilla y preservar sus resultados dentro
de `response_strategies/benchmark_results/`. Ademas del ATT, conviene revisar:

- `Port_Waiting_Statistics.csv`
- `Service_Route_Utilization.csv`
- `Average_Vessel_State_Counts.csv`
- `Average_Origin_Waiting_TEU_By_OD.csv`
- `Average_In_Transit_TEU_By_OD.csv`

## Validacion

Pruebas del proyecto:

```powershell
python -m pytest -q
```

Pruebas de la libreria local:

```powershell
python -m pytest o2despy\tests -q
```

Auditoria inicial del 3 de septiembre de 2026:

- 210 pruebas pasan al excluir la prueba del calculador de resiliencia.
- `test_resilience_kpi_calculator.py` importa un modulo
  `resilience_kpi_calculator` que no esta incluido en la carpeta.
- `test_dashboard_launcher.py` todavia espera la constante antigua
  `DASHBOARD_URL`, aunque Round 2 ahora calcula el puerto dinamicamente.

Estos dos hallazgos no deben corregirse como parte de una estrategia
competitiva salvo autorizacion expresa.

## Diferencias Importantes Frente A Round 1

- La red tiene 9 rutas de servicio en lugar de 7.
- Las disrupciones y ventanas temporales son diferentes.
- La ruta `S4` tiene tres segmentos; una estrategia de Round 1 que use indices
  antiguos, por ejemplo el segmento 6, no se puede copiar literalmente.
- El dashboard selecciona un puerto disponible en vez de asumir siempre 8000.
- Round 2 incluye mas pruebas del modelo y validaciones de estrategia.

Las ideas de Round 1 se pueden reutilizar, pero cada ruta, indice, ventana de
disrupcion y referencia de booking debe recalcularse con los datos de Round 2.
