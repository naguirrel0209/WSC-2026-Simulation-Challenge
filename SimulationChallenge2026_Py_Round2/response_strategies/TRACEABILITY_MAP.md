# Mapa de trazabilidad - Round 2

Fecha de corte: 2026-09-03

## Cadena principal

```text
Reglas Round 1
    -> limites documentados en README.md y AGENTS.md
    -> auditoria de entradas, configuracion, escenario y pruebas
    -> hipotesis aislada en response_strategies/user_strategy.py
    -> copia inmutable de la variante + SHA-256
    -> simulacion con semilla 2026 y configuracion oficial
    -> log + 8 CSV por experimento completo
    -> calculo de ATT, ventanas, espera, flujo, rutas y buques
    -> decision: promover, rechazar o abortar
    -> estrategia ganadora restaurada como archivo activo
```

## Reglas y configuracion

| ID | Fuente | Requisito verificado | Evidencia |
|---|---|---|---|
| R1 | Reglas de Round 1 | Cambios competitivos solo en `response_strategies/` | `README.md`, `AGENTS.md` |
| R2 | Contrato de estrategia | No crear/eliminar legs o buques; bookings consistentes | `response_strategies/strategy_validation.py` y 209 pruebas aplicables |
| C1 | `config/simulation_config.py` | Warm-up 140, medicion 360, intervalo 5 | SHA-256 `D1E320...1A16` |
| C2 | `main.py` | Semilla 2026 | comandos de corrida y logs |
| C3 | `scenario_builders/disruption_scenario.py` | 3 tramos congestionados y 2 puertos cerrados | SHA-256 `7ADBB...8487` |
| C4 | Salida estadistica | 72 periodos por corrida completa | CSV ATT de E0, E1, E2 y E3 |

Los documentos de raiz fueron creados por solicitud expresa del usuario. Las
implementaciones y este informe permanecen dentro de la zona competitiva.

## Huellas de entradas oficiales

| Archivo | SHA-256 |
|---|---|
| `Input/demand_matrix.csv` | `B385A9FAFE17F6076B01DB595782C75154E5F578D83CCF150242C6E6EE523D2E` |
| `Input/input_summary.csv` | `474F31812F3934A7B8E051BE23CCF186893DE1CBF6BC3F4F300A3E0147D176DC` |
| `Input/ports.csv` | `FB9D1A47D507DAD0F0AF3AAC26DB0A79B7EB4405CB385042742E8A933D4DDB72` |
| `Input/route_plan.csv` | `C22C1ED0F8ACDEC48D1D0038AEA51D3464823A60922F2C7EEF4678D58F8AB4B6` |
| `Input/route_segments.csv` | `746EE3FF6F84E73B3842A65B50DE736E4FF43CCCF860D94F59B2814A6E5734C8` |
| `Input/service_routes.csv` | `32ED9028F90AF2B975053F82481784CC3A754F402BB84E29CFEFC5261A60E135` |
| `Input/vessel_classes.csv` | `68589CBB356CFA3B6E138FBE310B620D534F813D2E5BF72634BE1662C667523E` |
| `config/simulation_config.py` | `D1E32030620C57FE88008DA981AA942E318A87A408119BA1CB7847B5D8261A16` |
| `scenario_builders/disruption_scenario.py` | `7ADBBDE77FEA55BEDEFFE3D0CCCD1DACB4010F4DC5AF3FCAE208CFEC72758487` |

Estructura auditada: 20 puertos, 9 rutas, 54 segmentos, 6 clases de
buque, 41 buques declarados por el escenario y matriz de demanda 20 x 20.

## Matriz experimento-evidencia-decision

| ID | Hipotesis | Hash de estrategia | Evidencia | Resultado | Decision |
|---|---|---|---|---:|---|
| E0 | Control default | plantilla sin personalizacion | `benchmark_results/00_default_first_run/` | 15.5322 | referencia |
| E1 | Distancia + headway + transferencia reduce ATT | `57523537...B210` | `benchmark_results/01_expected_time_booking/` | **15.2756** | promover |
| E2a | Rebooking global 35d evita carga atrapada | `4C88B55E...A04B` | `benchmark_results/02a_full_proactive_35d_aborted_day305/` | sin KPI | abortar |
| E2 | Exclusion futura solo en booking nuevo evita costo de E2a | `68D8DA95...F7E5` | `benchmark_results/02_selective_proactive_booking/` | 15.7336 | rechazar |
| E3 | Riesgo futuro gradual evita desvios bruscos | `1EAB25BC...B5B5` | `benchmark_results/03_risk_penalized_booking/` | 15.5908 | rechazar |

Cada carpeta completa contiene:

- `user_strategy.py` y `__init__.py` usados en la corrida;
- `simulation.log`;
- `ATT_By_Statistics_Interval.csv`;
- `Baseline_ATT_By_Statistics_Interval.csv`;
- `Average_In_Transit_TEU_By_OD.csv`;
- `Average_Origin_Waiting_TEU_By_OD.csv`;
- `Average_Vessel_State_Counts.csv`;
- `Cumulative_Completed_TEU_By_OD.csv`;
- `Port_Waiting_Statistics.csv`;
- `Service_Route_Utilization.csv`.

Excepciones:

- E0 preserva los ocho CSV, pero la corrida inicial no archivo log ni copia de
  estrategia.
- E2a preserva estrategia y log parcial; no contiene CSV finales porque fue
  detenida en el dia 310.

## Auditorias

| Auditoria | Momento | Controles | Resultado |
|---|---|---|---|
| A0 | Antes del analisis | reglas, estructura, baseline, primera corrida | conforme; dos defectos de pruebas preexistentes |
| A1 | Antes de E1 | hashes, referencias, contratos, pruebas | conforme |
| A2 | Antes de E2 | hashes, no cambios de motor, 72 periodos E1, pruebas | conforme |
| A3 | Antes de E3 | hashes, no cambios de motor, 72 periodos E2, hashes de archivo, pruebas | `209 passed, 2 deselected` |
| A4 | Despues de restaurar E1 | compilacion, hash activo, pruebas | conforme; hash activo igual a E1 |

## Pruebas conocidas

La suite aplicable se ejecuta con:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  --ignore=simulation_model\tests\test_resilience_kpi_calculator.py `
  -k "not test_dashboard_launcher and not test_enabled_strategy_uses_default_strategy_before_disruption" `
  -q
```

Resultado final: `209 passed, 2 deselected`.

Hallazgos fuera de la estrategia competitiva:

| ID | Hallazgo | Impacto | Tratamiento |
|---|---|---|---|
| T1 | Falta `resilience_kpi_calculator` | la suite completa falla en coleccion | no corregido por limite de alcance |
| T2 | La prueba del dashboard usa `main.DASHBOARD_URL`, ya inexistente | una prueba legacy falla | no corregido por limite de alcance |
| T3 | Una prueba espera fallback default antes de disrupcion | incompatible con una politica personalizada de booking global | se registra y excluye de la evaluacion competitiva |

## Comando reproducible

Ejemplo de corrida aislada:

```powershell
.\.venv\Scripts\python.exe -u -c `
  "from pathlib import Path; import main; main.OUTPUT_DIRECTORY = Path(r'response_strategies\benchmark_results\ID_EXPERIMENTO'); main.run_simulation()"
```

El directorio debe existir y contener antes de la corrida una copia de
`user_strategy.py`. Al finalizar se copia tambien
`Output/Baseline_ATT_By_Statistics_Interval.csv`.

## Estado actual

| Elemento | Estado |
|---|---|
| Estrategia activa | E1 tiempo esperado |
| Archivo activo | `response_strategies/user_strategy.py` |
| SHA-256 activo | `57523537F49EEDFAFD81B38E5576815AB6BC089E0CDC15A856D178475305B210` |
| Mejor ATT | `15.2756` dias |
| Control default | `15.5322` dias |
| Mejora | `0.2566` dias, `1.65%` |
| Proxima variante | N1 costo sensible a carga/capacidad |

## Continuacion del proyecto

Para cada nueva variante:

1. Partir de E1 y crear un nuevo ID, sin sobrescribir evidencia existente.
2. Formular una sola hipotesis y sus criterios de aceptacion.
3. Repetir hashes y suite aplicable antes de correr.
4. Archivar codigo y hash antes de ejecutar.
5. Exigir 72 periodos, `Simulation completed.` y ocho CSV.
6. Comparar contra E0 y E1, tanto globalmente como por cinco ventanas.
7. Revisar espera por puerto, completado, transito, rutas y buques.
8. Promover solo si mejora ATT sin acumulacion extrema ni costo no viable.

La especificacion de N1, N2 y N3 esta en `EXPERIMENT_REPORT.md`.
