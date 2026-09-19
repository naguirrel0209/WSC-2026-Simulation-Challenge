> Retirada del 18 de septiembre de 2026: se eliminaron del código de trabajo
> integrated_strategy.py, test_integrated_strategy.py, validate_integrated.py
> y run_integrated_experiment.py por solicitud del usuario. H1 sigue activa.
> Las fuentes, pruebas y resultados archivados se conservan como historia.
> Las referencias a esos archivos y comandos en el texto siguiente son históricas.
> Ver [STRATEGY_OPTIONS.md](STRATEGY_OPTIONS.md). No ejecutar simulaciones.
> Para comprobaciones sin avance sigue disponible validate_onboard_cost.py.

> Actualización del 14 de septiembre de 2026: la evaluación completa posterior
> rechazó la candidata frente a H1 (ATT +4.55%; pérdida +107.94%). Consultar
> [INTEGRATED_EVALUATION.md](INTEGRATED_EVALUATION.md). La entrada conserva H1.
> El contenido siguiente registra la validación anterior a esa corrida.

# Validacion de los tres mecanismos

**Validacion final: 95 pruebas pasadas, una excluida**, en 9.09 segundos de
pytest. Inicio: 2026-09-14 05:23:30 UTC (2026-09-13 23:23:30 Guatemala).
Incluye la actualizacion posterior de AGENTS.md solicitada expresamente
por el usuario, su registro documental y cinco casos adicionales de integridad.

Comando ejecutado sin simulacion:

```powershell
.\.venv\Scripts\python.exe -B response_strategies/validate_integrated.py
```

Registro final reproducible:
[validation.json](benchmark_results/integrated_mechanisms_20260913/validation_20260914T052330_657007Z_5db09ecd/validation.json),
[unit_tests.log](benchmark_results/integrated_mechanisms_20260913/validation_20260914T052330_657007Z_5db09ecd/unit_tests.log).
La misma carpeta contiene los hashes antes/despues, comprobaciones historicas
y copias de las fuentes y pruebas tomadas antes de ejecutarlas.

No hubo llamadas a Model.run, Model.warmup ni a las diez entradas bloqueadas
de avance de Sandbox. Ningun archivo vigilado cambio durante las pruebas.
Se comprobaron los manifiestos historicos originales, los archivos protegidos,
las salidas del control/observadas, los CSV actuales y H1 activa. Las 67 pruebas
anteriores de H1/H2/integridad siguen pasando, junto con 23 casos competitivos
nuevos y cinco de integridad documental. La primera validacion competitiva
(90 pasadas, una excluida, 5.57 segundos) se conserva intacta en
`validation_20260914T051823_729270Z_ee57fdbe/`.

AGENTS.md no figuraba en el manifiesto original de 163 archivos. Su nueva
comprobacion documental es adicional: no elimina ni cambia ninguna de las
156 comparaciones historicas estrictas. `authorized_documentation_changes.json`
identifica la solicitud, el hash previo y el hash autorizado. Se verifica
tambien la copia de AGENTS.md anterior a esta modificacion. El registro
rechaza cualquier ruta distinta de AGENTS.md y no puede eximir al motor,
configuracion, entradas ni baseline. La verificacion final capturo el AGENTS.md
actualizado antes de ejecutar pruebas.

## Codigo agregado

[integrated_strategy.py](integrated_strategy.py) contiene la candidata
`IntegratedStrategy`, que combina:

- La penalizacion finita de H2 para conexiones operativas.
- Todos los costes de transferencia dentro de la busqueda y la comparacion,
  sin duplicar las esperas ni las 18 horas fijas.
- El tiempo de navegacion por segmento, ponderado por su multiplicador,
  para decidir entre ruta lenta y desvio.

Se mantiene H1 para la carga embarcada: tanto el plan actual como una
continuacion candidata a bordo excluyen la espera ficticia de otro servicio.
El campo de distancia fisica conserva su valor; otro campo contiene la
distancia ponderada. La estrategia no cambia legs, buques, configuracion,
semilla, intervalos ni umbrales.

El grafo admite legs lentos y conserva la clave real de las disrupciones al
filtrar rutas alternativas. Puertos cerrados, falta de flota utilizable,
indices invalidos y tramos desconectados siguen siendo imposibles. Las
pruebas incluyen cambio y caducidad de disrupcion dentro del mismo bloque
del cache, y restauracion del coste cuando vuelve el multiplicador normal.

Los casos de rebooking comprueban prefijo completado, indice actual,
referencias inversas, rollback, tres segmentos circulares de S4 y un
transbordo que solo se acepta cuando su coste completo compensa.

## Alcance y continuidad

Esta es una candidata **conjunta H1+H2+H3**, solicitada al pedir agregar los
tres mecanismos. Su control futuro es H1. No atribuir un futuro cambio
de KPI a un mecanismo individual sin experimentos separados.
La especificacion de coste/control se documento antes de programar en
[INTEGRATED_MECHANISMS.md](INTEGRATED_MECHANISMS.md).

`user_strategy.py` sigue apuntando a H1 para conservar la restriccion anterior
de no sustituir la entrada activa. La candidata conjunta esta implementada y
validada, pero una ejecucion normal de main.py continuaria usando H1.
La H2 aislada, el control previo a H1 y las evidencias anteriores conservan
sus bytes. Ninguna simulacion ni operacion Git de escritura fue ejecutada.

El validador compartido ahora admite suites/fuentes adicionales y una carpeta
de experimento por argumento. Su comando anterior conserva la misma suite;
`validate_integrated.py` agrega las pruebas nuevas y registra sus propias
fuentes/resultados sin sobrescribir los anteriores.

La auditoria final de esta tarea esta en
[task_audit.json](benchmark_results/integrated_mechanisms_20260913/task_audit.json).
H2 y H1 ya tenian cambios y artefactos pendientes de la tarea anterior:
se preservaron y se compararon con el estado al iniciar esta solicitud.
Esta nota se actualizo despues de la validacion; no se cambio codigo competitivo
despues del resultado inicial de 90 pruebas. La segunda validacion comprueba
el mismo codigo competitivo y la ampliacion documental del validador.

ATT y KPI de la candidata siguen **sin medir**. Para evaluarlos hace falta
una futura corrida autorizada y la revision de ventanas, puertos, maximos
de acumulacion, carga de rutas y estados individuales de los 41 buques.
