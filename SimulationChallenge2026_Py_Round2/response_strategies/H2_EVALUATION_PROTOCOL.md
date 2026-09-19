# Protocolo para una futura evaluacion autorizada de H2

Este documento diseña la evaluacion; no autoriza ni ejecuta simulaciones.
La estrategia activa permanece H1. H2 se comparara exclusivamente con el
control anterior a H1, con H1 y H3 desactivadas. Para estudiar H1+H2 se
necesitaria otro experimento expresamente autorizado y su propio control.

## Preparacion que puede repetirse sin simular

Desde la raiz del proyecto:

```powershell
.\.venv\Scripts\python.exe -B response_strategies/validate_onboard_cost.py
.\.venv\Scripts\python.exe -B response_strategies/analyze_h2_evidence.py
```

El primer comando solo ejecuta pruebas seleccionadas con todos los metodos
de avance bloqueados. El segundo importa solamente librerias estandar,
lee los archivos historicos y genera una nueva carpeta `analysis_*`.
Ninguno modifica `Output/`. Cada nueva ejecucion conserva sus resultados.

Si una comprobacion historica falla, detenerse e investigar la diferencia.
No refrescar hashes de entradas, motor o baseline ni sobrescribir el control.
No usar pytest sin seleccion ni `validate_resilience.py --tests-only`.

## Diseno de comparacion

1. Solicitud futura explicita para simular el control y H2 aislada.
2. Primero repetir el control con instrumentacion de observacion. Conservar
   sus resultados y decidir limites de acumulacion antes de observar H2.
3. Ejecutar H2 con exactamente la misma instrumentacion y configuracion.
   Proceso Python nuevo para cada corrida, para reiniciar caches y aleatoriedad.
4. Conservar las referencias historicas como contexto. Si el nuevo control
   no reproduce sus CSV/KPI, investigar procedencia, entorno y diferencias
   antes de atribuir cambios a H2. No ajustar la candidata para acomodar
   diferencias no explicadas.
5. Una replica H1 sin ajustes solo serviria para su atribucion pendiente;
   no sustituye el control de H2.

## Registro obligatorio antes de iniciar cada proceso

Crear una carpeta nueva y exclusiva bajo `response_strategies/benchmark_results/`.
Guardar antes de construir el modelo:

- Variante: `control_pre_h1` o `h2_isolated`; identificador y hora UTC/local.
- Copias y SHA-256 de entrada activa, clase elegida, copia base, helpers
  `default_strategy.py`/`strategy_validation.py`, formula y lanzador/observadores.
- `protected_hashes.json` original y manifiesto fresco de todo el proyecto
  salvo Git, entornos y la carpeta nueva. Registro separado de documentos.
- Version de Python, dependencias, plataforma y comando exacto. Git solo lectura.
- Semilla 2026, warm-up 140 dias, medicion 360 dias, intervalo estadistico 5 dias.
  Conservar el avance diario usado por `main.run_simulation` y todas las ventanas.
- Copia de los ocho CSV anteriores y del baseline inalterado. Nunca recomputar
  el baseline ni modificar `Input/`, configuracion, escenario o motor.
- Hash de la clase realmente instalada en el proceso antes de cualquier avance.
  Una copia al terminar no sustituye esta evidencia.

## Seleccion de variante y corrida sin editar la entrada activa

El futuro lanzador debe residir dentro de `response_strategies/`. Importar
`simulation_model` primero, como en las pruebas. El framework ya puede haber
importado la clase `UserStrategy`; por eso reasignar solo la variable de un
modulo no basta. Se puede mantener la identidad de esa clase y sustituir su
base **solo en memoria del proceso aislado**, por `h2_control_strategy.ResilienceStrategy`
o `h2_connection_strategy.H2ConnectionStrategy`. Restablecer `_context` y
`_state`, y comprobar la MRO y el origen de los tres metodos cambiados antes
de avanzar. No escribir ni sustituir `user_strategy.py`.

El ciclo reproducible, a implementar en ese lanzador tras autorizacion, es:

```text
importar y verificar la variante exacta; congelar copias, hashes y configuracion
crear escenario con scenario_builders.create_with_disruption()
construir Model(context, seed=2026)
instalar observadores sin cambiar decisiones, relojes, eventos ni RNG
warmup(period=timedelta(days=140))
reiniciar solo acumuladores del observador al comenzar la medicion
guardar estado inicial de los 41 buques y colas
para day = 1..360:
    Model.run(duration=timedelta(days=1))
    recoger muestras pasivas diarias sin avanzar mas tiempo
    cada 5 dias:
        calcular ATT con get_teu_weighted_average_transport_time_hours
            usando los limites reales del intervalo; dividir entre 24
        guardar fila con StartDay, EndDay, ATT sin redondear y ATT publicado
        guardar instantaneas de puertos/rutas/buques y contadores de decisiones
al terminar:
    write_all(sim, carpeta_nueva/Output)
    write_att_by_period(carpeta_nueva/Output, filas)
    copiar el baseline verificado a esa misma carpeta
    guardar estados finales, telemetria, log completo y manifiesto final
    verificar igualdad de archivos protegidos antes/despues
    marcar complete=true solo tras llegar a 360 dias y reconciliar 72 intervalos
```

Usar los escritores existentes, pasando una carpeta nueva dentro de strategies.
No invocar `main.main()`, que usa `Output/`, `Logs/` y abre el dashboard.
No ejecutar el esquema de arriba bajo la autorizacion de esta tarea.
El lanzador y los observadores futuros siguen por implementar y validar;
este documento fija su contrato y secuencia, no entrega un runner ya probado.

## Observaciones adicionales necesarias

| Registro | Campos y momento | Que permite verificar |
| --- | --- | --- |
| Decisiones de booking | hora, shipment, TEU, OD, puerto actual, buque, booking/indice anterior, alternativas con indices, ruta elegida, componentes de coste, rho, espera, headway, bloqueo por cierre/flota/leg lento, ganancia y razon | Frecuencia real del veto; primer transbordo infravalorado; distinguir prediccion de espera realizada |
| Transbordos realizados | descarga y siguiente carga, puerto, rutas entrante/saliente, TEU, espera realizada, rebookings repetidos | Si Shenzhen o Piraeus reciben mas carga, esperan mas por servicio o sufren conexiones fallidas |
| Colas | TEU de origen/transbordo separados, edad maxima, total, hora de cada cambio, maximo y duracion por encima del limite predefinido | Detectar acumulaciones ocultas por las medias y medir drenaje tras cada disrupcion |
| Servicios y alternativas | creacion/retirada, clave de disrupcion, buques asignados/pendientes, carga y capacidad, viajes vacios y duracion, TEU entregados | Alternativas persistentes sin carga, recuperacion de flota y falta de servicio local |
| 41 buques | ID, estado, ruta, ruta pendiente, segmento, puerto/leg, carga/shipments, berth, ultimo cambio | Identidades conservadas, estados exclusivos, carga coherente, retorno a rutas originales |
| Integridad de shipments | generados, completados, almacenados y embarcados, bookings ordenados e inversos | Conservacion de TEU, referencias duplicadas y contenedores sin itinerario operativo |

Las muestras diarias o cada cinco dias solo dan **maximos muestreados**.
Para maximos exactos se requiere observacion pasiva de cada cambio de cola,
carga y estado. No se pueden inferir maximos exactos de los ocho CSV actuales.
Instrumentar solo dentro de strategies, sin modificar el motor ni crear
eventos adicionales, y usar el mismo observador en control y H2. Validar
que no cambia el orden de eventos, los numeros aleatorios ni las decisiones.
Las trazas de H2 deben corresponder a decisiones realmente evaluadas, no a
recalculos posteriores con una cache o estado distinto.

## Calculos y criterio de decision

Emparejar filas por StartDay/EndDay y comprobar 72 intervalos de cinco dias,
sin duplicados ni huecos, hasta 360. Recalcular desde las mismas filas
redondeadas que el historico y guardar tambien resultados internos sin
redondear con nombres diferentes. No mezclar ambas precisiones.

```text
ATT_medio = media aritmetica de los 72 ATT de intervalo
KPI = suma((1 - ATT_baseline / ATT_variante) * (EndDay - StartDay + 1))
delta = candidata - control
```

Comparar ATT y KPI total, todos los intervalos individuales y las ventanas
41-100, 141-200, 216-240, 261-275, 276-320, 321-330 y 331-360. La ventana
261-360 es un subtotal de las ultimas cuatro; nunca sumarla otra vez.
Revisar ademas 96-105, 236-240, 191-195 y 346-350 por los retrocesos
observados, sin cambiar las ventanas predefinidas ni afinar la variante.

Exigir ATT medio y KPI total menores que el control comparable. Cualquier
retroceso local, mayor espera/transbordo o cola extrema mantiene la variante
en revision aunque mejore el total. Revisar los 20 puertos, con prioridad
Shenzhen, Piraeus, Shanghai, Colombo, Busan, Tianjin, Jebel Ali y Tanger Med;
carga de todas las rutas incluidas alternativas temporales; maximos, edad y
duracion de acumulacion; y estados de cada uno de los 41 buques.

Los limites para colas extremas, duracion de alternativas vacias y drenaje
deben fijarse tras la corrida instrumentada de control y **antes** de H2.
Si faltan esas observaciones, informar el cambio de ATT/KPI como provisional
y no aceptar una mejora competitiva comprobada. Un total medio de 41 buques
no sustituye la auditoria de sus 41 identidades.

Archivar log, ocho CSV, telemetria, fuentes de inicio, manifests, resultados
y retrocesos antes de cambiar la hipotesis. Si la corrida se interrumpe,
marcar `complete=false`: los estadisticos parciales no son una corrida
completa ni un checkpoint reanudable. H2 permanece sin KPI medido hasta
terminar una corrida autorizada y esta revision.
