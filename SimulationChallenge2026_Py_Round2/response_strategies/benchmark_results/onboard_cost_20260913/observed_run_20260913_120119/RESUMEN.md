# Resumen de la corrida terminada el 13 de septiembre de 2026

La corrida guardada termino a las 12:01:19, con 140 dias de warm-up y
360 dias medidos en 72 intervalos de cinco dias. El log confirma
`Simulation completed.` y una duracion de 15 minutos y 2 segundos.
Este analisis solo leyo resultados existentes; no ejecuto la simulacion.

| Indicador | Control previo a H1 | Corrida actual | Cambio |
| --- | ---: | ---: | ---: |
| ATT medio por intervalo, dias | 14.801806 | 14.435278 | -2.48%; -8.80 horas |
| KPI de perdida | 19.028839 | 11.820352 | -37.88% |
| TEU promedio en espera en puertos | 8,626 | 8,227 | -4.63% |
| TEU promedio esperando transbordo | 2,983 | 2,737 | -8.25% |
| TEU completados, suma de celdas OD redondeadas | 489,296 | 490,283 | +987 |
| Utilizacion media total de rutas | 3.55% | 3.54% | -0.01 puntos porcentuales |

El baseline tiene ATT medio de 13.854111 dias. La corrida actual queda
0.581167 dias (+4.19%) por encima de ese baseline sin disrupciones.

El ATT anterior y el actual son promedios de los 72 valores de intervalo
publicados en CSV. Cada intervalo contiene un ATT ponderado por TEU;
el promedio de intervalos no es una ponderacion global por todos los TEU.
La fila OverallMean del CSV actual indica 14.43: el escritor usa valores
internos sin redondear para esa fila. La pequena diferencia con 14.435278
recalculado desde las filas publicadas se debe al redondeo.

El KPI de perdida es `sum((1 - ATT_baseline / ATT_actual) * dias_intervalo)`.
Un valor menor es mejor; un aporte negativo supera el baseline de esa ventana.
11.820352 es el KPI de perdida, no el ATT ni un porcentaje.

| Ventana CSV | Contexto | ATT control | ATT actual | KPI control | KPI actual |
| --- | --- | ---: | ---: | ---: | ---: |
| 41-100 | Colombo-New Jersey | 13.430 | 13.564 | -0.326 | 0.266 |
| 141-200 | Shanghai-Kaohsiung | 17.288 | 16.532 | 11.519 | 9.399 |
| 216-240 | Qingdao-Busan | 13.640 | 13.714 | -0.834 | -0.693 |
| 261-275 | Cierre de Piraeus | 14.060 | 13.817 | 0.038 | -0.236 |
| 276-320 | Recuperacion posterior a Piraeus | 16.752 | 15.533 | 6.455 | 3.540 |
| 321-330 | Cierre de Tianjin y salida inmediata | 14.795 | 14.460 | 0.245 | 0.032 |
| 331-360 | Recuperacion final | 15.158 | 14.690 | 1.359 | 0.424 |
| 261-360 | Ultimos 100 dias, subtotal | 15.675 | 14.916 | 8.097 | 3.759 |

Las ventanas agrupan intervalos completos y no coinciden exactamente con
todos los limites de las disrupciones. La fila 261-360 es un subtotal;
no debe sumarse de nuevo a las cuatro filas anteriores.

La mejora se concentra en Shanghai-Kaohsiung y en la recuperacion posterior
a Piraeus. En 276-320 el ATT baja 1.219 dias y el KPI de esa ventana cae
45.16%. La ventana Shanghai-Kaohsiung sigue siendo la mas costosa, con
9.399 puntos de perdida. El pico de ATT permanece en 186-190: baja de
20.56 a 19.22 dias. Colombo-New Jersey y Qingdao-Busan presentan retrocesos
pequenos respecto del control.

| Puerto | TEU promedio en espera, control | Actual | Cambio |
| --- | ---: | ---: | ---: |
| Shanghai | 1,839 | 1,416 | -423 |
| Singapore | 1,194 | 1,128 | -66 |
| Shenzhen | 765 | 946 | +181 |
| Colombo | 624 | 569 | -55 |
| Piraeus | 469 | 516 | +47 |
| Busan | 494 | 472 | -22 |
| New Jersey | 473 | 397 | -76 |
| Tianjin | 155 | 153 | -2 |

Shenzhen concentra el mayor deterioro de espera: su componente de transbordo
sube de 207 a 420 TEU, mientras Shanghai baja de 1,257 a 863.
Piraeus sube de 228 a 281 TEU en espera de transbordo. Los valores son
promedios temporales, no TEU acumulados, colas finales ni maximos.
Los totales del CSV se calculan antes de redondear, por lo que pueden
diferir de la suma de sus celdas publicadas.

Las nueve rutas S1-S9 aparecen con carga positiva. S1 lleva 7,735 TEU
promedio frente a 7,593; S2 baja de 1,085 a 993 y S5 de 2,632 a 2,510.
La utilizacion sigue siendo baja en agregado (3.54%).
Los estados medios registran 38.82 buques navegando, 0.19 esperando atraque
y 1.98 atendidos; el total publicado es 41.00, con diferencias de redondeo
entre componentes. Estos CSV no permiten revisar el estado final individual
de los 41 buques ni descartar alternativas temporales sin carga.

La estrategia actual coincide con el hash de la H1 validada:
`bde16bfcd00ab5084beded9e99baa7a1d393b329306797be8211165daa2fac1b`.
La comparacion con el control muestra solamente el cambio de H1 en
`resilience_strategy.py`. Su ultima modificacion (11:37:42) precede
la creacion del log (11:46:17). Esto es consistente con una corrida H1,
aunque el log no registra el hash cargado al iniciar y la copia de codigo
archivada aqui se tomo despues de completar la corrida.

De los 163 archivos del manifiesto del control, 156 conservan su hash,
incluidos entradas, configuracion, escenario, motor y baseline.
Solo difieren los siete CSV generados por la nueva corrida.
La configuracion y main.py conservan semilla 2026, warm-up 140,
medicion 360 e intervalos de cinco dias.

Se archivaron los ocho CSV, el log completo, la entrada y la estrategia
actual, con hashes de la copia. Los ocho CSV archivados se verificaron
contra Output/. Los datos detallados estan en metrics.json.
No se modificaron estrategias ni parametros y no se ejecuto una nueva
corrida. Los resultados muestran una mejora observada frente al control,
con retrocesos locales; la atribucion exacta y los maximos de acumulacion
tienen las limitaciones indicadas arriba.
