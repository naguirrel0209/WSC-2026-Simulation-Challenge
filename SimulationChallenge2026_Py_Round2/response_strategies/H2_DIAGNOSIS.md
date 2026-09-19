# Diagnostico y candidata H2 aislada

Trabajo del 13 de septiembre de 2026, hora de Guatemala. Los nombres de las
verificaciones usan UTC; algunas carpetas corresponden al 14 de septiembre UTC.
No se ejecuto ninguna simulacion. Git se uso solo para status, diff y log.
La revision inicial encontro el arbol de trabajo limpio.

## Evidencia recalculada

Se leyeron los ocho CSV de cada archivo historico y sus `metrics.json`.
El calculo reproducible esta en [analyze_h2_evidence.py](analyze_h2_evidence.py)
y su salida integra, con hashes, filas leidas, 72 intervalos, 20 puertos,
nueve rutas y matrices OD, en
[evidence.json](benchmark_results/h2_connections_20260913/analysis_20260914T003011_371319Z_fc97558a/evidence.json).
Ambos ATT y KPI recalculados coinciden con los `metrics.json` a tolerancia
de 1e-10. Se compararon las claves StartDay/EndDay, sin incluir los pies CSV.

| Medida | Control previo a H1 | Corrida observada consistente con H1 |
| --- | ---: | ---: |
| ATT medio de 72 intervalos, dias | 14.801806 | 14.435278 |
| KPI de perdida | 19.028839 | 11.820352 |
| Espera media total en puertos, TEU | 8,626 | 8,227 |
| Espera media de transbordo, TEU | 2,983 | 2,737 |
| Utilizacion total, % | 3.55 | 3.54 |

El ATT de cada intervalo es ponderado por TEU. Su promedio aritmetico entre
intervalos no es el ATT global ponderado por todos los TEU. El KPI es
`sum((1 - ATT_baseline / ATT_escenario) * dias_intervalo)`, no ATT ni porcentaje.
El baseline medio es 13.854111 dias. El pie `OverallMean=14.43` observado usa
valores internos sin redondear; el recalculo usa las 72 filas publicadas.

| Ventana CSV | ATT control | ATT observado | KPI control | KPI observado |
| --- | ---: | ---: | ---: | ---: |
| 41-100 | 13.430000 | 13.564167 | -0.325868 | 0.265637 |
| 141-200 | 17.288333 | 16.531667 | 11.519402 | 9.399215 |
| 216-240 | 13.640000 | 13.714000 | -0.834392 | -0.692636 |
| 261-275 | 14.060000 | 13.816667 | 0.037967 | -0.236388 |
| 276-320 | 16.752222 | 15.533333 | 6.454586 | 3.539823 |
| 321-330 | 14.795000 | 14.460000 | 0.245437 | 0.032033 |
| 331-360 | 15.158333 | 14.690000 | 1.359374 | 0.423524 |
| 261-360, solo subtotal | 15.674500 | 14.915500 | 8.097363 | 3.758991 |

Las ventanas son globales de calendario, no ATT de un unico leg u OD. Sus
bordes agrupan intervalos y no coinciden exactamente con todos los cierres.
Hay deterioros dentro de ventanas que mejoran: 191-195 aumenta 0.44 dias,
y 346-350 aumenta 0.47. El mayor retroceso individual es 96-100 (+1.11 dias),
seguido por 101-105 (+0.62); 236-240 aumenta 0.51. Esto justifica observar
tambien la salida de las disrupciones, ademas de sus promedios.

## Hechos, mecanismos posibles y datos faltantes

**Shenzhen.** Espera total 765 a 946 TEU (+181); transbordo 207 a 420 (+213),
origen 558 a 525 (-33). La suma de diferencias puede variar por redondeo.
Segun `Input/route_segments.csv`, conecta S1, S2 y S5. Shanghai conecta esas
rutas y S4, y su espera de transbordo baja de 1,257 a 863. En las medias por
ruta, S1 transporta 142 TEU mas, S2 92 menos y S5 122 menos. Es compatible con
una redistribucion de conexiones; no identifica que shipments cambiaron
de ruta, en que sentido, cuando ni por que. Los 0.00 buques esperando en
Shenzhen estan redondeados y no prueban ausencia de espera o falta de salidas.

**Piraeus.** Espera total 469 a 516 (+47), transbordo 228 a 281 (+53) y
origen 242 a 234 (-8). Buques esperando: 0.09 a 0.12 en promedio. Conecta
S1 y S7; S1 visita Piraeus dos veces por ciclo. S7 transporta 48 TEU mas
en promedio. Jebel Ali sube 33 TEU en espera de origen y Tanger Med sube
31 TEU en transbordo. Las matrices OD muestran mayor carga media en transito
Rotterdam-Jebel Ali (224 a 241) y Tanger Med-Jebel Ali (107 a 119).
Los OD y puertos pertenecen a la misma red, pero las matrices no identifican
el puerto intermedio ni el periodo de espera. No demuestran que el cierre
de Piraeus o una decision H1 causara estos cambios.

**Colombo-New Jersey.** La ventana 41-100 retrocede 0.134167 dias de ATT.
S5 contiene el leg afectado. La exclusividad actual de rutas sin legs
congestionados puede forzar conexiones por S1/S6 o S7/otros servicios;
es una posibilidad topologica, no una ruta observada en los CSV. El OD
Colombo-New Jersey sube de 89 a 94 TEU medios en transito durante toda
la medicion. Ese dato no explica por si solo el pico de 96-100.

**Qingdao-Busan.** La ventana 216-240 retrocede 0.074 dias; su ultimo
intervalo 236-240 sube 0.51. S9 contiene el leg afectado y S2 ofrece un
itinerario mas largo entre esos puertos. El veto de conexiones puede
eliminar alternativas operativas que combinen S2/S9. Faltan horarios,
itinerarios individuales y costes de decisiones para comprobarlo.

**Shanghai-Kaohsiung.** Sigue siendo la ventana mas costosa (KPI 9.399215)
y mantiene el pico 186-190 (19.22 dias). S4 tiene tres segmentos; S2 conecta
Shanghai, Xiamen, Shenzhen, Kaohsiung y Busan. El desvio y las conexiones
son mecanismos plausibles para desplazar espera a otros puertos. La actual
exclusion de legs con multiplicador mayor que uno no compara navegar lento
con desviarse: eso corresponde a H3, que sigue pendiente y desactivada.

## Hallazgos de codigo que motivan H2

En [resilience_strategy.py](resilience_strategy.py), `_edge_cost` usa media
separacion como holgura: con espera de 8 h veta un servicio cada 12 h y
admite uno cada 48 h. Un servicio frecuente no informa la hora del proximo
buque, por lo que ese veto no demuestra imposibilidad de conexion.

`adjust_bookings_before_cargo_handling` pide un camino como si fuera una
asignacion de origen. Cuando cambia de ruta, comprueba que el coste completo
sea finito, pero solo suma 18 h. Omite la penalizacion por ocupacion de la
primera transferencia. Corregir solo el coste despues de la busqueda tampoco
garantiza elegir el mejor camino: la continuacion a bordo puede quedar
descartada, y la cache origen/destino no distingue el buque del que llega.

`_snapshot` actualiza por bloques de seis horas y usa ocupacion de atraques,
espera observada y flota desplegada como proxies. No contiene un calendario
de arribos ni reservas de capacidad. No se retocaron esos mecanismos ni sus
umbrales. Se necesitan trazas futuras para saber con que frecuencia se
activa el veto, que costes omite y si explica los retrocesos agregados.

## Implementacion y aislamiento

La [hipotesis y formula](H2_HYPOTHESIS.md) se guardaron antes del codigo.
[h2_control_strategy.py](h2_control_strategy.py) es una copia exacta del control
previo a H1, SHA-256 `a387c563fb91e77b7f5010e4a3f3b43ca772f4e4d58c80ab5c7be3f5245d502b`.
La regla local `.gitattributes` preserva los bytes de esa copia en futuras
operaciones Git autorizadas. No se realizo ninguna operacion Git de escritura.

[h2_connection_strategy.py](h2_connection_strategy.py) hereda de esa copia.
Sustituye el veto por una penalizacion de holgura faltante y considera el
coste completo desde la busqueda, incluida su cache. La primera conexion
en otra ocurrencia del mismo puerto/ruta se trata como transferencia si su
indice de salida no es el siguiente del buque. Esto evita fusionar bookings
de segmentos incompatibles. Las transferencias posteriores conservan la
definicion por booking del control; no se introduce una nueva politica de flota.

El booking actual mantiene media separacion (H1 desactivada en H2). Se
mantienen cierres, falta de flota, exclusion de legs lentos y clave de
disrupcion (H3 desactivada). Los hooks de atraque/flota y todos los umbrales
se heredan sin cambios. `user_strategy.py` y `resilience_strategy.py`
siguen byte a byte iguales a H1 observada.

## Validacion y limites de la entrega

[validate_onboard_cost.py](validate_onboard_cost.py) conserva su comando,
ahora delega en [validate_connections.py](validate_connections.py).
La copia del validador anterior esta en
`benchmark_results/h2_connections_20260913/validate_onboard_cost_before.py`.
No se reemplazaron los resultados historicos de 25 pruebas de H1.

El validador fija los hashes de los dos manifiestos historicos. Comprueba
156 archivos contra el control (incluido baseline), los ocho CSV archivados
del control, los once elementos del snapshot observado y los ocho CSV
actuales contra ese snapshot. Comprueba tambien la entrada H1 y la copia
base H2. Documentos protegidos se registran aparte y cualquier diferencia
se rechaza: al inicio de esta tarea ninguno diferia del control.

Cada ejecucion guarda un manifiesto nuevo antes/despues, errores de integridad,
log y hashes en carpeta unica. Las ejecuciones finales tambien capturan
copias de codigo, pruebas y formula antes de probar. Se vigilan archivos
no versionados y caches. Se excluyen Git, entornos de dependencias y la
propia carpeta nueva de resultados. Las fixtures que alteran hashes trabajan
unicamente sobre copias en el directorio temporal de esa verificacion.

Se bloquean `Model.run`, `Model.warmup` y diez entradas de avance de Sandbox
antes de recolectar las pruebas. Se usa `-B`, pytest sin cache ni plugins
automaticos y se excluye la prueba de diez dias por nombre completo.
La primera ejecucion paso 64 pruebas, excluyo una y tuvo cero llamadas de
avance y cero cambios durante pruebas. El registro final se identifica en
[H2_VALIDATION.md](H2_VALIDATION.md).

Los CSV disponibles son promedios temporales. No proporcionan maximos,
colas finales, duracion de acumulaciones, transferencias por shipment ni
estados individuales finales de 41 buques. Solo S1-S9 con carga positiva
aparecen en el resumen; eso no descarta alternativas temporales vacias.
El snapshot de H1 fue capturado despues de la corrida: su log no identifica
el hash cargado al inicio. No se atribuye causalidad exacta ni se afirma
una replica independiente.

H2 no tiene ATT ni KPI medidos. Los ejemplos unitarios comprueban decisiones
y contratos; no prueban mejora competitiva. El
[protocolo futuro](H2_EVALUATION_PROTOCOL.md) detalla los datos faltantes.
