# Revision de la corrida terminada el 13 de septiembre de 2026, 23:43:51

La simulacion termino completa: 140 dias de warm-up, 360 dias medidos y 72
intervalos. El log registra 15 min 55 s de ejecucion. No se ejecuto ninguna
simulacion ni prueba durante esta revision.

## Comparacion con la corrida anterior

Los ocho CSV coinciden byte por byte con las salidas de la corrida anterior,
terminada a las 18:53:53. La comparacion usa el manifiesto guardado a las
23:23:30, antes de esta nueva corrida, en la validacion de los mecanismos
integrados. Tambien coinciden con la corrida archivada de las 12:01:19.
El baseline es un archivo previo; los otros siete CSV tienen fecha de
modificacion de las 23:43:51.

| Indicador | Anterior, 18:53 | Ultima, 23:43 | Cambio |
| --- | ---: | ---: | ---: |
| ATT medio por intervalo, dias | 14.435278 | 14.435278 | 0.00% |
| KPI de perdida | 11.820352 | 11.820352 | 0.00% |
| TEU medios esperando en puertos | 8,227 | 8,227 | 0.00% |
| TEU medios esperando transbordo | 2,737 | 2,737 | 0.00% |
| Utilizacion total reportada | 3.54% | 3.54% | 0.00 puntos |

Se conserva la mejora observada respecto al control anterior a H1: ATT de
14.801806 a 14.435278 dias (-2.48%, unas 8.80 horas) y KPI de 19.028839 a
11.820352 (-37.88%). Esa mejora ya existia; esta corrida no agrega otra.

El ATT es el promedio de las 72 filas redondeadas publicadas, no un nuevo
promedio ponderado por todos los TEU. El KPI se recalcula como
`sum((1 - ATT_baseline / ATT_actual) * dias_intervalo)`; no es ATT ni porcentaje.

## Estrategia activa

`response_strategies/user_strategy.py` sigue definiendo `UserStrategy` como
subclase de `ResilienceStrategy`: la entrada normal conserva H1.
`IntegratedStrategy`, con los tres mecanismos solicitados, sigue separada.
Se conservo asi en la entrega previa para mantener la entrada activa.

Los hashes actuales de la entrada, H1 y la candidata integrada coinciden con
la validacion anterior al inicio de esta corrida. Los resultados son
consistentes con otra ejecucion de H1. El log no registra el hash cargado al
iniciar; las copias de codigo en `sources_after_run/` fueron tomadas despues.
No presentarlas como un registro de carga del proceso.

La candidata integrada tiene 95 pruebas unitarias pasadas y una excluida en
el registro previo. Sus ATT y KPI siguen sin medir en estas evidencias.

## Debilidades que persisten

| Ventana global | ATT ultima, dias | KPI ultima | KPI control previo a H1 |
| --- | ---: | ---: | ---: |
| 41-100 | 13.564167 | 0.265637 | -0.325868 |
| 141-200 | 16.531667 | 9.399215 | 11.519402 |
| 216-240 | 13.714000 | -0.692636 | -0.834392 |
| 261-275 | 13.816667 | -0.236388 | 0.037967 |
| 276-320 | 15.533333 | 3.539823 | 6.454586 |
| 321-330 | 14.460000 | 0.032033 | 0.245437 |
| 331-360 | 14.690000 | 0.423524 | 1.359374 |
| 261-360, solo subtotal | 14.915500 | 3.758991 | 8.097363 |

Todas estas ventanas son identicas a la corrida inmediatamente anterior.
El subtotal 261-360 no debe sumarse otra vez a sus ventanas componentes.

- La ventana 141-200, que coincide con la disrupcion Shanghai-Kaohsiung,
  sigue aportando 9.399 puntos de perdida. El pico de ATT es 19.22 dias en
  186-190. Es la primera prioridad de evaluacion.
- En 276-320, despues del cierre de Piraeus, el ATT sigue en 15.533 dias y
  el aporte de perdida es 3.540. Conviene observar la recuperacion y las
  conexiones pendientes; los agregados no prueban su causa.
- Shenzhen conserva 946 TEU medios esperando, frente a 765 en el control
  previo a H1. Su transbordo pasa de 207 a 420. Piraeus conserva 516 frente
  a 469 TEU totales y 281 frente a 228 de transbordo. Son regresiones respecto
  al control original, no aumentos nuevos de esta ultima corrida.
- Las ventanas 41-100 y 216-240 mantienen pequenos retrocesos frente al
  control original: +0.134 y +0.074 dias de ATT. El intervalo 96-100 empeora
  1.11 dias; 236-240 empeora 0.51. Un total mejor no elimina esos costes.

Las ventanas son globales de calendario, no mediciones causales de un unico
OD. Los CSV de espera son medias, no maximos ni colas finales. La utilizacion
agregada de 3.54% no demuestra disponibilidad en cada conexion. El total medio
de 41 buques tampoco audita los estados finales individuales ni descarta
alternativas temporales sin carga.

## Proximas estrategias de mejora

1. Evaluar la candidata integrada ya preparada, con H1 como control. Antes
   de una futura corrida autorizada, seleccionar explicitamente esa variante
   en la entrada y guardar la copia y el hash exactos antes del arranque.
   Una ejecucion normal con la entrada actual sigue seleccionando H1.
2. Medir los tres mecanismos existentes: penalizacion finita de conexiones
   operativas, coste completo de transferencia desde la busqueda y navegacion
   lenta frente a desvio usando cada distancia y su multiplicador. Apuntan
   a defectos de decision identificados en el codigo; su beneficio de red
   aun debe comprobarse. No agregar otros ajustes antes de medirlos.
3. Revisar todas las ventanas anteriores, con especial atencion a Shanghai,
   recuperacion de Piraeus y transbordos de Shenzhen. Si mejora la candidata
   conjunta, usar variantes separadas para identificar el aporte de cada
   mecanismo; no atribuir un cambio conjunto a uno solo.
4. En una futura corrida autorizada, registrar desde la estrategia los costes
   de continuar/cambiar, decisiones de booking, espera y antiguedad de carga,
   maximos de cola, carga de alternativas y estados de los 41 buques. Estas
   observaciones permiten decidir despues si hace falta ajustar la estimacion
   de llegadas o la politica de recuperacion. Mantener los umbrales actuales.

## Evidencia e integridad

`evidence.json` conserva los calculos, hashes, comparacion contra el manifiesto
previo y auditoria del control original. Se guardaron los ocho CSV, el log
completo y las fuentes observadas despues de la corrida en esta carpeta.

De los 163 archivos del manifiesto original, 156 coinciden y siete son los CSV
generados que ya diferian tras H1. No hay diferencias inesperadas de entradas,
configuracion, escenario, motor o baseline. AGENTS.md tuvo una actualizacion
documental autorizada previa, fuera de ese manifiesto original; no se edito
en esta revision. La revision solo creo esta nueva carpeta de evidencia dentro
de response_strategies; no cambio la entrada activa ni ejecuto operaciones Git
de escritura.
