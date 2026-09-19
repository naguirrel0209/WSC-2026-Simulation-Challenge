> Retirada del 18 de septiembre de 2026: se eliminaron del código de trabajo
> integrated_strategy.py, test_integrated_strategy.py, validate_integrated.py
> y run_integrated_experiment.py por solicitud del usuario. H1 sigue activa.
> Las fuentes, pruebas y resultados archivados se conservan como historia.
> Las referencias a esos archivos y comandos en el texto siguiente son históricas.
> Ver [STRATEGY_OPTIONS.md](STRATEGY_OPTIONS.md). No ejecutar simulaciones.
> Para comprobaciones sin avance sigue disponible validate_onboard_cost.py.

# Tres mecanismos combinados: candidata acumulativa

Especificacion escrita antes de implementar, 2026-09-13. La solicitud actual
es agregar los tres mecanismos descritos al usuario. Se prepara una candidata
conjunta H1+H2+H3 en `integrated_strategy.py`, conservando H1 como entrada activa
y la H2 aislada anterior sin cambios. No se autoriza ni ejecuta simulacion.
La solicitud actual permite esta combinacion de mecanismos en una candidata;
no se presenta como un experimento aislado de H2 ni H3.

## Control y comportamiento

Control de la futura comparacion conjunta: H1 activa, SHA-256
`bde16bfcd00ab5084beded9e99baa7a1d393b329306797be8211165daa2fac1b`.
La ultima corrida termino el 13 de septiembre a las 18:53:53 y sus ocho CSV
son identicos a la corrida archivada de las 12:01:19: ATT 14.4352777778 dias
y KPI de perdida 11.8203520321. Son referencias observadas; los logs no
registran el hash de la estrategia cargada al inicio. H2 aislada conserva
su propio control anterior a H1 y su formula documentada.

1. Conexion operativa: sustituir el veto por penalizacion finita de holgura
   faltante. No descartar automaticamente servicios frecuentes.
2. Coste completo: incluir espera de servicio, espera de puerto, ocupacion,
   riesgo de conexion y las 18 h fijas una sola vez, desde la busqueda.
3. Leg lento: permitirlo cuando sea navegable, valorar cada distancia con su
   propio multiplicador y elegir entre continuar y desviarse por coste total.

## Formula fijada

```text
T_navegacion = sum(distancia_i * multiplicador_i) / velocidad_media_ruta
s = headway / 2
P_rho = 24 * max(0, (rho - 0.80) / (1 - 0.80))
P_conexion = max(0, 1.5 * espera_puerto - s)
C = T_navegacion + espera_servicio + espera_puerto
    + transferencia * (18 + P_rho + P_conexion)
```

`espera_servicio = 0` solo para la continuacion ya embarcada y `s` para
subirse a un servicio. El mismo tratamiento de H1 se aplica al booking
pendiente y a una candidata que sigue a bordo; no se inventa una espera
de nuevo embarque al comparar esas dos continuaciones. Los bookings
posteriores mantienen su coste completo de conexion. No se cambia ningun
umbral: ganancia minima `max(12, 0.1*C_nuevo)` y las escalas de H2 anteriores.

No se pondera toda una ruta por un unico multiplicador: solo cada segmento
afectado. El headway conserva el calculo de ciclo del control, que ya usa
multiplicadores. La distancia fisica y la distancia ponderada son campos
distintos del edge; el coste usa la ponderada una sola vez.

Puertos cerrados, indices invalidos, ciclos desconectados o falta de
velocidad/flota utilizable siguen siendo imposibles. Las alternativas se
filtran con la **clave real de disrupcion activa**, incluidos los legs lentos,
aunque esos legs ya no se veten. No vaciar la coleccion de disrupciones para
admitir navegacion lenta. El cache se invalida cuando cambia esa clave o un
multiplicador, incluso dentro del mismo bloque de seis horas.

## Pruebas y evaluacion

Casos sin avance: conexion frecuente viable; costes que cambian el ganador;
continuacion lenta que aun gana; desvio que si compensa; ponderacion de varios
legs con multiplicadores diferentes; cierre intermedio; flota ausente;
alternativa de clave obsoleta; caducidad de disrupcion; S4 circular;
bookings completados y futuros; indices/referencias inversas y rollback.

Congelar fuentes y manifiestos antes/despues en una carpeta nueva. Bloquear
Model.run, Model.warmup y entradas de avance de Sandbox, usar Python -B y
pytest sin cache, y excluir la prueba de diez dias. Conservar los resultados
previos de H1 y H2 y todos los CSV actuales. Git solo lectura.

La evaluacion futura sigue las medidas y observaciones de
[H2_EVALUATION_PROTOCOL.md](H2_EVALUATION_PROTOCOL.md), pero cambia el control
de esta candidata conjunta a H1 y debe identificar expresamente H1+H2+H3.
Comparar ATT, KPI, ventanas 41-100, 141-200, 216-240, 261-275, 276-320,
321-330, 331-360 y subtotal 261-360; espera/transbordo por puerto, carga de
rutas, maximos de acumulacion y estados individuales de los 41 buques.
No atribuir a un mecanismo individual el resultado de una combinacion.
La candidata conjunta no tiene KPI medido y permanece sin activar.
