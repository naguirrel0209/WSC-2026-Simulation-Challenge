# Posibles estrategias sobre H1

Estado del 18 de septiembre de 2026: H1 sigue siendo la entrada activa.
Su referencia observada es ATT 14.435278 días y KPI de pérdida 11.820352.
La candidata conjunta fue retirada del código de trabajo por solicitud del usuario.
Su corrida fallida (ATT 15.091667; KPI 24.579206) y las fuentes exactas se conservan
como evidencia histórica. No se ejecutó ninguna simulación en esta retirada.

Estas son hipótesis para evaluar, no mejoras demostradas. No se implementan en
esta entrega. Cada experimento futuro necesita una autorización para simular,
una sola modificación conceptual y un control H1 explícito.

## Orden propuesto

| Prioridad | Estrategia | Cambio que se probaría | Evidencia que decidiría su utilidad |
| --- | --- | --- | --- |
| 1 | Coste completo del primer transbordo | Incluir desde la búsqueda el coste de cambiar de servicio, con espera y ocupación contadas una sola vez. Conservar el veto actual de conexiones, la exclusión de tramos lentos y todos los umbrales de H1. | Menos cambios de ruta con beneficio aparente; menor ATT/KPI y menor espera de transbordo en Shenzhen y Piraeus. |
| 2 | Estimación de la próxima salida | Comparar el tiempo estimado hasta un buque utilizable a partir de posiciones, velocidad, estado y observaciones disponibles, en lugar de usar siempre media separación entre servicios. | Menor error entre espera estimada y realizada; mejora de las conexiones en Shanghai, Shenzhen y Singapore. |
| 3 | Espera de carga por servicio | Incorporar el tiempo estimado para embarcar los TEU que ya esperan en el servicio de salida, usando capacidad y frecuencia locales. Distinguir esta espera de la cola de atraque y evitar duplicarla en el coste. | Reducción de espera, máximos y carga pendiente por puerto sin trasladar la acumulación a otro nodo. |
| 4 | Alternativas con despliegue factible | Comprobar que existe un buque transferible y un puerto compatible antes de proponer una alternativa; mantener la flota de 41 y la conectividad de los ciclos. | Alternativas que efectivamente reciben buques y transportan carga; mejora en el cierre de Piraeus y en 276-320, sin deteriorar el servicio donante. |
| 5 | Atraque orientado a entregas finales | Probar una prioridad que considere TEU que terminan su transporte y trabajo de descarga por hora, además de la antigüedad ya usada por H1. Se cambia la regla de selección, no el umbral de congestión ni el orden de carga del motor. | Menor demora de entregas y mejor recuperación en 276-360 sin perjudicar los transbordos ni posponer indefinidamente otros buques. |
| 6 | Navegación lenta aislada | Evaluar únicamente la posibilidad de continuar por un tramo lento frente al desvío: suma de distancia de cada segmento por su multiplicador, dividida por velocidad. Conservar las decisiones de conexión de H1. | Mejora en 41-100 y 141-200 sin repetir las regresiones de 191-195 o de la recuperación final. |

## Por qué empezaría por la primera

En H1, adjust_bookings_before_cargo_handling obtiene una ruta como si fuera una
asignación desde origen. Si la primera conexión cambia de servicio, comprueba
que su coste completo sea finito, pero luego suma únicamente las 18 horas fijas.
La penalización de ocupación de esa primera transferencia no se incorpora al
valor comparado. Corregir solo el total después de buscar tampoco garantiza
escoger la mejor opción: el contexto del primer tramo debe formar parte de
la búsqueda y de su caché.

Esta propuesta es más acotada que la candidata retirada: no sustituye el veto
por una penalización finita, no admite tramos lentos y no modifica políticas
de flota o atraque. Debe conservar la ventaja de H1 para la carga ya embarcada.
Su efecto sobre el KPI sigue sin estar probado.

## Precauciones de diseño de las otras opciones

- Próxima salida significa una estimación basada en información disponible.
  No usar realizaciones aleatorias futuras, modificar eventos del motor ni
  afirmar que existe un horario exacto cuando no está expuesto por la API.
- La espera por carga debe diferenciar origen, transbordo y servicio de salida.
  Una utilización baja de toda la red no garantiza un buque útil en un puerto
  y momento determinados. Definir la fórmula antes de medir la candidata.
- S1-ALT-1 y S7-ALT-1 aparecieron sin buques ni carga en las muestras diarias
  261-360 de la candidata rechazada. H1 histórica no tiene esa misma telemetría;
  investigar primero si el problema también ocurre en H1. No atribuirle a H1
  ese hallazgo sin medirlo.
- H1 ya prioriza antigüedad por TEU descargable y trabajo de servicio. Una
  variante de atraque debe aportar un criterio distinto, por ejemplo entregas
  finales, y vigilar el perjuicio posible a la carga que necesita conexiones.
- La navegación lenta se deja al final porque fue parte de la combinación
  fallida. Ese resultado no demuestra que H3 aislada sea mala ni que sea la
  causante de la regresión. Hay que conservar cierres, disponibilidad de flota,
  índices circulares de S4 y la clave real de disrupción.
- No reactivar la H2 aislada existente como si fuera H1 más una corrección:
  esa variante conserva su control anterior a H1 y es otro experimento.

## Medición común para cualquier experimento futuro

Mantener semilla 2026, calentamiento 140 días, medición 360 días e intervalos de
cinco días. No cambiar entradas, motor, escenario ni umbrales. Guardar primero
fuentes y hashes, y archivar todo antes de otra variante.

Comparar ATT medio por intervalo, KPI total, TEU completados y ventanas 41-100,
141-200, 216-240, 261-275, 276-320, 321-330 y 331-360; 261-360 es solo un subtotal.
Revisar también 191-195, 236-240, 96-105 y 346-350. No aceptar una mejora total
sin analizar sus regresiones locales.

Medir por separado espera de origen/transbordo, colas máximas, carga de rutas
alternativas, recuperación y estados de los 41 buques. Para edad pendiente,
excluir shipments con completion_time definido: la lista del puerto también
puede conservar entregas ya completadas. No cambiar el modelo para obtener
estas observaciones.

Fuentes locales: resilience_strategy.py; H2_DIAGNOSIS.md; y
[resultado integrado rechazado](benchmark_results/integrated_evaluation_20260915T052345_579591Z/RESUMEN.md).

