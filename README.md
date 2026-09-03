# WSC 2026 Simulation Challenge

Monorepo con las tres entregas del WSC 2026 Simulation Challenge. Cada ronda
es un proyecto Python independiente con sus propios datos, configuracion,
modelo, estrategias y resultados.

## Rondas

| Ronda | Carpeta | Descripcion |
|---|---|---|
| 0 | [`SimulationChallenge2026_Py_Round0/`](SimulationChallenge2026_Py_Round0/) | Proyecto y escenario inicial |
| 1 | [`SimulationChallenge2026_Py_Round1/`](SimulationChallenge2026_Py_Round1/) | Primera ronda competitiva y estrategias historicas |
| 2 | [`SimulationChallenge2026_Py_Round2/`](SimulationChallenge2026_Py_Round2/) | Segunda ronda, experimentos y estrategia activa |

La documentacion especifica de cada ronda se encuentra en su propio
`README.md` cuando esta disponible.

## Ejecucion

Desde PowerShell, entra en la ronda que quieras ejecutar:

```powershell
cd SimulationChallenge2026_Py_Round2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Los resultados de la ultima simulacion se escriben en `Output/`. Cada ronda
incluye un dashboard local dentro de `dashboard/`.

## Regla competitiva

Las soluciones de competencia deben modificarse solamente dentro de
`response_strategies/`. No se deben alterar entradas, configuracion, escenario
o motor para mejorar resultados.

El punto principal de implementacion es:

```text
response_strategies/user_strategy.py
```

## Resultados de Round 2

- [Informe completo de experimentos](SimulationChallenge2026_Py_Round2/response_strategies/EXPERIMENT_REPORT.md)
- [Mapa de trazabilidad](SimulationChallenge2026_Py_Round2/response_strategies/TRACEABILITY_MAP.md)
- [Resultados archivados](SimulationChallenge2026_Py_Round2/response_strategies/benchmark_results/)

La mejor estrategia validada actualmente es `01_expected_time_booking`, con
ATT medio de `15.2756` dias frente a `15.5322` del control default.

## Flujo de trabajo Git

Ejecuta Git desde la raiz de este monorepo o desde cualquiera de las carpetas
de ronda:

```powershell
git add .
git commit -m "Describe el cambio"
git push
```

Los entornos virtuales, caches de Python y logs operativos estan excluidos por
el `.gitignore` de la raiz.
