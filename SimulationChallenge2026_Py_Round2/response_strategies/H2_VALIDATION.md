# Verificacion final sin simulacion

Resultado: **67 pruebas pasadas, una excluida**, en 5.40 segundos de pytest.
Hora UTC de inicio: 2026-09-14 00:36:15 (2026-09-13 18:36:15 Guatemala).
Python 3.13.15 y pytest 9.1.1 del entorno del proyecto.

Comando ejecutado desde la raiz:

```powershell
.\.venv\Scripts\python.exe -B response_strategies/validate_onboard_cost.py
```

Registro final:
[validation.json](benchmark_results/h2_connections_20260913/validation_20260914T003615_598559Z_0c8fdc52/validation.json),
[unit_tests.log](benchmark_results/h2_connections_20260913/validation_20260914T003615_598559Z_0c8fdc52/unit_tests.log),
[historical_checks.json](benchmark_results/h2_connections_20260913/validation_20260914T003615_598559Z_0c8fdc52/historical_checks.json).
Esa misma carpeta contiene manifiestos antes/despues y `sources/` con copias
de los diez archivos de entrada, estrategia, formula, validadores y pruebas
capturadas antes de ejecutarlas.

- Cero llamadas a `Model.run` y `Model.warmup`, ambos bloqueados explicitamente.
- Cero llamadas a las diez entradas de avance/warm-up de Sandbox bloqueadas.
- Ningun archivo vigilado cambio durante las pruebas.
- 156 archivos comprobados contra el control original, incluido baseline.
- Ocho CSV del control y once elementos del snapshot observado verificados.
- Los ocho CSV actuales coinciden con los observados archivados.
- Manifiestos historicos verificados contra sus hashes originales fijos.
- H1 activa y copia base de H2 verificadas, sin cambiar sus bytes.
- `candidate_kpi: null`: H2 no se ha simulado.

Se excluyo explicitamente
`test_bookings_connect_and_replace_reverse_references`, que avanza diez dias.
Pytest se ejecuto sin cache, sin plugins automaticos y con temporales dentro
de la carpeta nueva de verificacion. Los casos de integridad alteran y borran
archivos solo en sus copias temporales, nunca en archivos reales protegidos.
Esas copias son fixtures adversariales, no corridas ni controles alternativos.

La primera verificacion de esta tarea, anterior a ampliar las comprobaciones
de manifiestos y captura de fuentes, queda intacta en
`validation_20260914T002831_642770Z_1b810cde/`: 64 pasadas y una excluida.
No hubo fallos unitarios en estas dos ejecuciones. Los errores de lanzamiento
del entorno restringido se resolvieron usando el ejecutable del proyecto con
escalacion aprobada. El Python empaquetado se uso solo para el analisis CSV,
porque no incluye pytest. No se instalaron dependencias.

## Cobertura significativa

Los tests nuevos de H2 comprueban que un servicio frecuente operativo gana
al servicio lento antes favorecido por el veto; que el coste completo impide
un transbordo con ganancia ficticia; que la busqueda cambia de ganador segun
el buque de llegada; y que encuentra otra conexion cuando una carece de flota.
El borde de ganancia de 12 h comprueba que no se suman dos veces espera ni
transferencia. Se cubren cierre de origen/destino, falta de velocidad/flota,
snapshot real sin Model, veto de legs lentos mantenido, prefijo completado,
indices circulares de S4, ocurrencias distintas de un puerto en la misma
ruta, limpieza de referencias inversas y rollback ante fallo de escritura.

Se verifico expresamente que H1 esta ausente de H2: el coste restante del
booking actual sigue aumentando con la media separacion, como el control.
Los hooks de atraque/flota y umbrales son los mismos objetos/metodos heredados.
Las pruebas previas de H1 y de contratos tambien pasaron. Las pruebas del
calculador faltante y de DASHBOARD_URL quedan fuera de esta seleccion; no
se corrigieron ni se presentan como reevaluadas.

## Trazabilidad y cambios posteriores a las pruebas

La candidata H2 validada tiene SHA-256:
`587b4994a530c8d386f2a9a8f4ffcd3b92508642feea428d47c79ed11ba0ff96`.
La copia base pre-H1:
`a387c563fb91e77b7f5010e4a3f3b43ca772f4e4d58c80ab5c7be3f5245d502b`.
H1 activa conserva:
`bde16bfcd00ab5084beded9e99baa7a1d393b329306797be8211165daa2fac1b`.

Despues de las pruebas se agrego esta nota y se extendio `.gitattributes`
para preservar los bytes de los nuevos archivos de evidencia en futuras
operaciones Git autorizadas. No se cambio codigo competitivo tras validarlo.
La comparacion final de toda la tarea esta en
[task_audit.json](benchmark_results/h2_connections_20260913/task_audit.json),
con los manifiestos `task_before.json` y `task_after.json`. Documenta por
separado los cambios permitidos, archivos protegidos y archivos historicos.

El resultado solo demuestra integridad y comportamiento en casos unitarios.
La mejora de ATT/KPI, maximos de acumulacion, carga temporal de alternativas
y estados finales de los 41 buques siguen pendientes del
[protocolo futuro](H2_EVALUATION_PROTOCOL.md).
