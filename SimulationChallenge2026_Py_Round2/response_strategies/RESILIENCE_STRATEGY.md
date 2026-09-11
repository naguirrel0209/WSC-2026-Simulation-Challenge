# Estrategia de resiliencia — Round 2

`user_strategy.py` expone `ResilienceStrategy`. La política anterior se conserva
sin cambios en `expected_time_reference.py`. No se modifica Round1.

## Decisiones implementadas

- Atraque: suma de edad en horas por TEU **descargable en la escala actual**,
  dividida por horas estimadas de operación. Se estima carga elegible desde
  almacenamiento y capacidad restante; productividad igual a la fórmula del
  modelo (45 TEU/h por grúa; grúas según LOA). Empates por espera y orden original.
- Booking: caminos de tiempo esperado, con navegación, media frecuencia entre
  servicios, espera estimada y coste de transbordo. Sobre rho=0.80 se añade una
  penalización gradual (hasta 24 h para rho=1). Una conexión se descarta si su
  holgura estimada es menor a 1.5 veces la espera. Sin camino, el envío espera
  un nuevo intento; no se salta la restricción mediante el fallback.
- Rebooking: revisa carga embarcada por antigüedad, conserva la parte recorrida,
  combina tramos consecutivos del mismo servicio y exige mejora superior a
  12 horas y al 10% del coste alternativo. Reemplazo transaccional de referencias.
- Flota: espera proyectada mayor a 84 horas (incluye puerto completamente cerrado)
  activa evaluación de alternativas mediante el constructor del framework.
  Solo usa legs y buques existentes, conserva el protocolo de transferencia de
  buques vacíos y restaura servicios tras la disrupción. Valida ciclos y revierte
  cambios si falla. Congestión sin disrupción reconocida no fuerza un ciclo nuevo.

## Límites de observación y acciones

El API no expone rho=lambda/mu ni horarios de salida/ETA. Se usa ocupación
instantánea de atraques abiertos como **proxy de rho**; no es una estimación
estadística de utilización. La espera se aproxima con trabajo de buques en
servicio y observaciones de cola recibidas en el hook de atraque, que caducan
a las seis horas. El estado se refresca cada seis horas, al observar colas,
al cambiar disponibilidad, multiplicadores o composición de flota.

La holgura usa media separación entre servicios: ciclo estimado / buques / 2.
No garantiza una conexión concreta. No se consulta el calendario futuro de
disrupciones: los filtros del framework utilizan únicamente planes activos.

**No es posible reservar capacidad ni imponer oldest-first al embarcar** con
los cuatro hooks existentes. El motor selecciona greedy desde su OrderedSet
de señales, por orden de inserción; no hay un hook de selección de carga. No se
reordena esa colección, no se parchean métodos y no se alteran estados de carga.
La prioridad por edad se aplica al atraque y al examen del rebooking; no debe
presentarse como una garantía de embarque por antigüedad.

La edad pendiente afecta el numerador del ATT (TEU-tiempo). Su denominador es
TEU elegibles; el denominador del cociente de pérdida es el ATT del escenario.

## Seguridad y coste

Fallback ante atributos faltantes/valores inválidos, con contadores de errores
consultables mediante `UserStrategy.state(context).errors`. No se silencian
errores sin registrarlos. Cambios de bookings y flota se revierten si fallan.
Los errores de flota retornan decisión de no actuar, evitando una segunda
mutación automática sin guardas. Caché de caminos por OD y estado observado;
un contexto nuevo reinicia toda la memoria de la política.

## Validación

`validate_resilience.py --tests-only` ejecuta pruebas de contratos y política.
Sin esa opción, ejecuta el escenario original con semilla 2026, warm-up 140,
360 días e intervalos de 5 días leídos de configuración, y escribe todos los
artefactos dentro de `response_strategies/benchmark_results/resilience_*`.
No ejecuta `main.py`, para no escribir en Output ni Logs ni abrir un servidor.
Usa el mismo Model y avance diario. Comprueba hashes de archivos protegidos.
Guarda ATT parcial y `progress.json` cada cinco días medidos. Solo
`summary.json` y `complete: true` indican una corrida terminada. Los resultados
parciales no permiten reanudar el estado interno del modelo tras detener Python.

Conserva Output anterior, baseline y código de la variante; calcula la pérdida
por período desde CSV (misma precisión que el dashboard). La comparación con
Output es contra resultados guardados, no una réplica recién ejecutada del
control. Una sola semilla no demuestra mejora en la evaluación oficial.
