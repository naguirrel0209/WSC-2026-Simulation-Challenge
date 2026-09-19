# H2: conexiones operativas con coste completo

Definida el 2026-09-13 antes de implementar la candidata. Experimento pendiente
de una autorizacion futura para simular. La entrada activa sigue siendo H1.

## Mecanismo y formula fijada

El control previo a H1 veta un transbordo si `h/2 < 1.5*w`. Con `w=8 h`,
rechaza un servicio cada 12 h y admite uno cada 48 h, aunque no conoce sus
horarios. Ademas, al replanificar comprueba el coste de transferencia pero
solo suma 18 h a un camino seleccionado como si partiera del origen.
Esto omite la penalizacion de ocupacion del primer transbordo y puede
seleccionar el camino equivocado incluso si se corrige su coste despues.

Una unica hipotesis H2: valorar las conexiones operativas con un coste finito
y completo tanto al seleccionar como al comparar el plan.

Para un edge operativo, todas las cantidades en horas:

```text
s = h / 2
P_rho = 24 * max(0, (rho - 0.80) / (1 - 0.80))
P_conexion = max(0, 1.5*w - s)
C(edge, transferencia) = distancia / velocidad + s + w
                         + transferencia * (18 + P_rho + P_conexion)
```

Se reutilizan exactamente los umbrales 0.80 y 1.5 y la escala de 24 h del
control. La holgura faltante sustituye al veto, sin coeficiente nuevo.
`s + P_conexion = max(s, 1.5*w)` para una transferencia: mejorar la
frecuencia nunca aumenta este componente. Es un proxy de riesgo, no un
horario, probabilidad de perder el buque ni prediccion calibrada.

Sin velocidad/flota utilizable o con puerto cerrado, el coste es infinito.
Se mantiene la exclusion actual de legs lentos y la clave de disrupcion de
alternativas (H3 desactivada). El booking actual conserva `h/2` exactamente
como el control previo a H1 (H1 desactivada en esta candidata).

En asignacion inicial el primer edge no es transferencia. Al llegar con
carga, el primero es transferencia salvo que continue en la misma ruta
y en el segmento siguiente del buque. Todos los edges posteriores conservan
el tratamiento de conexiones del control. La busqueda y su cache incluyen
ese contexto inicial. Se suma el coste de cada edge una sola vez; no se
anaden otras 18 h ni otra espera tras seleccionar el camino. El coste
restante del plan usa la misma formula para bookings futuros.

## Control, comportamiento esperado y criterio de evaluacion

Control unico: `benchmark_results/onboard_cost_20260913/control/`.
SHA-256 de su estrategia:
`a387c563fb91e77b7f5010e4a3f3b43ca772f4e4d58c80ab5c7be3f5245d502b`.
Se conserva una copia exacta en `h2_control_strategy.py`; la candidata
`h2_connection_strategy.py` hereda de esa copia, no de H1.

Se espera admitir conexiones frecuentes viables antes vetadas y evitar
transbordos cuya supuesta ganancia desaparece al incluir ocupacion y riesgo.
No se predice mejora cuantitativa de ATT o KPI con los agregados disponibles.
Shenzhen y Piraeus son prioridades de observacion, no causas demostradas.

Pruebas previas: decisiones con servicios de distinta frecuencia, coste
completo que cambia el ganador, segunda alternativa viable, cierres, falta
de flota, coste contado una vez, bookings ya completados, vuelta circular
S4, referencias inversas, transaccion atomica y contrato de bookings.

En la futura comparacion aislada exigir reduccion de ATT medio y KPI total
con semilla 2026, warm-up 140, medicion 360 e intervalos de 5 dias. Revisar
por separado 41-100, 141-200, 216-240, 261-275, 276-320, 321-330 y 331-360;
261-360 es solo subtotal. Cualquier retroceso local exige explicacion antes
de aceptar la variante. No aceptar acumulaciones extremas, alternativas
persistentes sin carga ni estados inconsistentes. Los limites de acumulacion
se fijaran con observaciones del control antes de ver resultados H2.
H1 observada es contexto secundario, no el control causal de H2 aislada.
