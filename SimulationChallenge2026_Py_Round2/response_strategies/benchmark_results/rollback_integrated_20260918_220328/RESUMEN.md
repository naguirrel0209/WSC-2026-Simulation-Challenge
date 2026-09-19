# Retirada de candidata integrada — 18 de septiembre de 2026

Se eliminaron del código de trabajo integrated_strategy.py, test_integrated_strategy.py,
validate_integrated.py y run_integrated_experiment.py. Se conservaron copias exactas
como texto en files_before_removal y todos los archivos históricos de la corrida.

H1 y sus CSV siguen intactos: KPI observado 11.820352 y ATT 14.435278 días.
La H2 aislada anterior conserva sus archivos y sigue sin ser la entrada activa.
Se actualizaron las notas de continuidad de la candidata retirada y se creó
../../STRATEGY_OPTIONS.md con seis hipótesis priorizadas para futuras tareas.

Verificación: 17 archivos Python analizados por AST, sin importaciones pendientes
a módulos retirados; 465 archivos vigilados conservan sus hashes. La comprobación
independiente de controles históricos, motor, entradas, configuración, baseline y
H1 no presenta diferencias. El alcance excluye cachés y temporales de pruebas cuyo
acceso está restringido; se detalla en audit.json.

No se ejecutaron simulaciones, warm-up, pruebas con avance ni operaciones Git de
escritura. No se implementó ninguna de las estrategias propuestas.
