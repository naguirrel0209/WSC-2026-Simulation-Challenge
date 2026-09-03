# Informe completo de experimentos - Round 2

Fecha de corte: 2026-09-03

## Resumen ejecutivo

La mejor estrategia valida es `01_expected_time_booking`, con ATT medio de
`15.2756` dias. Mejora el default en `0.2566` dias (`1.65%`), reduce la espera
total en `1,157 TEU` (`11.69%`) y completa `627 TEU` mas. Esta variante quedo
activa en `response_strategies/user_strategy.py`.

Las dos variantes de anticipacion no superaron ese resultado:

- La exclusion anticipada selectiva obtuvo `15.7336` dias (`1.30%` peor que
  default). Su principal regresion fue la ventana de Tianjin: `18.8400` dias.
- La penalizacion gradual de riesgo obtuvo `15.5908` dias (`0.38%` peor que
  default y `2.06%` peor que la ganadora).
- La proactividad completa con rebooking continuo se aborto en el dia 310 por
  costo computacional no viable y no produjo un KPI final.

La evidencia indica que el problema principal es la eleccion y sincronizacion
de bookings, no la capacidad global ni las colas de atraque. La utilizacion
total se mantiene entre `3.50%` y `3.58%`, y solo `0.20-0.24` buques esperan
atraque en promedio.

## Condiciones comunes

- Semilla: `2026`.
- Warm-up: `140` dias.
- Medicion: `360` dias.
- Intervalo estadistico: `5` dias, `72` periodos por corrida completa.
- Escenario: tres tramos congestionados y dos cierres portuarios oficiales.
- Zona modificada para competir: solo `response_strategies/`.
- Baseline estable medio: `13.8541` dias.

Antes de cada corrida se verificaron hashes, estructura de datos, ausencia de
cambios en el motor y pruebas aplicables. La auditoria final de la estrategia
ganadora reporta `209 passed, 2 deselected`.

## Resultados globales

| ID | Estrategia | ATT dias | vs default | vs baseline | Espera TEU | Completado TEU | Utilizacion | Desv. periodos | Tiempo reportado |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| E0 | Default inicial | 15.5322 | referencia | +12.11% | 9,894 | 487,606 | 3.50% | 1.99 | 00:20:59* |
| E1 | Tiempo esperado | **15.2756** | **-1.65%** | +10.26% | **8,737** | **488,233** | 3.57% | 2.21 | 00:23:26 |
| E2a | Proactiva completa 35d | sin KPI | abortada | sin KPI | sin KPI | sin KPI | sin KPI | sin KPI | 02:07:50 al dia 310 |
| E2 | Proactiva selectiva | 15.7336 | +1.30% | +13.57% | 9,625 | 485,516 | 3.58% | 2.37 | 00:35:36 |
| E3 | Riesgo gradual | 15.5908 | +0.38% | +12.54% | 9,581 | 486,194 | 3.55% | 2.21 | 00:45:50** |

`*` El tiempo de E0 se observo en la corrida original, pero su log no fue
archivado; sus ocho CSV si estan preservados.

`**` E3 sufrio una suspension del equipo de aproximadamente 22 minutos. El
reloj de pared la incluye; el consumo de CPU observado fue cercano a 23
minutos y no hubo atasco algoritmico.

## Resultados por disrupcion

Cada valor es la media de los intervalos de cinco dias que intersectan la
ventana oficial. Menor es mejor.

| Ventana | Default | E1 tiempo esperado | E2 selectiva | E3 riesgo |
|---|---:|---:|---:|---:|
| Colombo -> New Jersey | 13.7615 | **13.3238** | 13.3923 | 13.4400 |
| Shanghai -> Kaohsiung | 18.7331 | 19.1262 | **18.5369** | 18.8308 |
| Qingdao -> Busan | 14.8517 | 14.2433 | 14.8167 | **14.2400** |
| Cierre Piraeus | 14.4200 | **14.1875** | 14.6550 | 14.2950 |
| Cierre Tianjin | 15.7967 | **15.3767** | 18.8400 | 16.3300 |

E1 gana tres ventanas y queda practicamente empatada con E3 en Qingdao-Busan.
Su unica regresion clara es Shanghai-Kaohsiung (`+0.3931` dias frente a
default), pero sus mejoras restantes compensan esa perdida.

## Flujo, espera y capacidad

E1 frente a E0:

- Espera en origen: `6,408 -> 5,945 TEU` (`-463`).
- Espera de transbordo: `3,486 -> 2,792 TEU` (`-694`).
- Espera total: `9,894 -> 8,737 TEU` (`-1,157`).
- Carga completada: `487,606 -> 488,233 TEU` (`+627`).
- Carga media en transito: `21,392 -> 20,765 TEU` (`-627`).
- Carga media transportada por rutas: `16,328 -> 16,446 TEU` (`+118`).

Los mayores puntos de espera de E1 fueron Shanghai (`1,436 TEU`), Singapore
(`1,212`), Shenzhen (`978`) y New Jersey (`827`). Frente al default, E1 reduce
Shanghai en `628 TEU`, Colombo en `207` y Singapore en `76`, aunque aumenta
Shenzhen en `86` y New Jersey en `33`.

La ruta alternativa `S4-ALT-1` transporto `304 TEU` en default y `258 TEU` en
E1. Por tanto, crear mas rutas alternativas sin una politica explicita de
asignacion o preposicionamiento no garantiza una mejora.

## Estrategias probadas

### E1 - Tiempo esperado

Hipotesis: la menor distancia nautica no siempre minimiza ATT; deben incluirse
frecuencia del servicio y transferencias.

El costo usa dias de navegacion, media espera por headway, limite de headway de
7 dias y penalizacion de 0.75 dias por booking. Las disrupciones activas siguen
siendo manejadas por los filtros y rebooking del default.

Resultado: hipotesis confirmada. Es la ganadora actual.

### E2a - Proactividad completa

Hipotesis: replanificar carga embarcada con 35 dias de anticipacion evita que
entre a una futura disrupcion.

Resultado: rechazada por escalabilidad. La reevaluacion en cada llegada de
buque produjo un costo creciente; se detuvo en el dia 310 sin CSV finales.

### E2 - Proactividad selectiva

Hipotesis: excluir tramos congestionados 35 dias antes y puertos cerrados 7
dias antes, solo para bookings nuevos, conserva el beneficio sin el costo de
E2a.

Resultado: computacionalmente viable, pero peor ATT. Mejoro Shanghai-Kaohsiung
y redujo algo la espera total, pero desplazo carga y genero una regresion severa
alrededor de Tianjin.

### E3 - Penalizacion gradual de riesgo

Hipotesis: una penalizacion finita y creciente evita los desvíos bruscos de E2.

Resultado: corrigio gran parte de la regresion de Tianjin de E2 (`18.84 ->
16.33`), pero no supero ni al default ni a E1. Rechazada como candidata activa.

## Revision de predicciones

| Estrategia prevista | Rango previo | Resultado | Evaluacion |
|---|---:|---:|---|
| Tiempo esperado/frecuencia | 15.1-15.3 | 15.2756 | Prediccion acertada |
| Anticipacion selectiva | 14.6-15.0 | 15.7336 | Optimista; traslado el atasco |
| Riesgo gradual | 14.9-15.2 | 15.5908 | Optimista; penalizo rutas utiles |

La leccion es que conocer una disrupcion futura no basta: la estrategia debe
comparar el ETA real de cada trayecto con la ventana, y tambien considerar la
carga ya comprometida en cada servicio.

## Top 5 actualizado

| Puesto | Estrategia | Estado | ATT esperado |
|---:|---|---|---:|
| 1 | Tiempo esperado + presion de carga/capacidad | pendiente | 15.00-15.20 |
| 2 | Tiempo esperado + solape ETA con disrupcion y cache | pendiente | 15.05-15.22 |
| 3 | Tiempo esperado E1 | probado | **15.2756 real** |
| 4 | Rebooking selectivo activo con costo E1 y cache | pendiente | 15.10-15.35 |
| 5 | Riesgo gradual E3 | probado | 15.5908 real |

Los rangos pendientes son hipotesis, no resultados. Deben validarse con la
misma semilla y el protocolo de auditoria.

## Tres siguientes implementaciones

### N1 - Costo sensible a carga y capacidad

Extender E1 con una penalizacion normalizada por TEU ya reservados, capacidad
desplegada y headway de cada ruta. El objetivo es conservar sus rutas rapidas
sin concentrar transbordos en Shanghai, Singapore y Shenzhen.

Criterio de aceptacion: ATT menor a `15.2756`, espera total no mayor a `8,737`
TEU y carga completada no menor a `488,233` TEU.

### N2 - Riesgo basado en ETA y con cache

Estimar el dia de llegada a cada tramo de la ruta candidata y penalizar solo si
su navegacion o escala intersecta una ventana futura. Cachear costos por
origen, destino, dia y estado de disrupcion para evitar el costo de E2a.

Criterio de aceptacion: mejorar Shanghai-Kaohsiung sin empeorar Tianjin mas de
`0.10` dias frente a E1, con tiempo de CPU comparable a E1.

### N3 - Rebooking activo selectivo

Usar el costo de E1 al llegar a puerto, pero solo para shipments cuyo booking
restante contiene un tramo o puerto actualmente afectado. Marcar el shipment
por epoca de disrupcion para no recalcularlo repetidamente.

Criterio de aceptacion: ATT menor a `15.2756`, ninguna ventana peor que E1 en
mas de `0.20` dias y corrida completa sin crecimiento superlineal.

## Uso de estrategias de Round 1

Si se pueden reutilizar los principios de Round 1:

- costo ponderado de ruta y frecuencia: ya transferido con exito en E1;
- rebooking ante disrupcion: reutilizable con alcance y cache estrictos;
- rutas alternativas y preposicionamiento: reutilizable solo tras recalcular
  ciclos, puertos y buques de Round 2;
- prioridad de atraque: legal, pero de bajo potencial con cola media de 0.20.

No se debe copiar codigo que dependa de indices de segmentos de Round 1. En
Round 2, por ejemplo, `S4` tiene tres segmentos y las ventanas son distintas.

## Recomendacion

Mantener E1 como control y siguiente punto de partida. Implementar N1 primero,
porque ataca el indicador que mas se movio con la mejora real: TEU esperando,
especialmente en transbordo. No combinar varias hipotesis en una sola corrida;
cada variante debe conservar codigo, hash, log y ocho CSV propios.
