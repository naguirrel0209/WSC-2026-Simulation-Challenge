"""Run with -B. Artifacts exclusively inside response_strategies/benchmark_results.

Usage: python -B response_strategies/validate_resilience.py [--tests-only]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / 'response_strategies/.validation_deps'), str(ROOT), str(ROOT / 'o2despy')]

import csv
import datetime as dt
import hashlib
import json
import shutil
import time
import simulation_model  # Initialize in the engine's normal order.
import pytest


def hashes():
    files = [p for p in ROOT.rglob('*') if p.is_file()
             and 'response_strategies' not in p.relative_to(ROOT).parts
             and '__pycache__' not in p.parts]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def loss(folder):
    def rows(name):
        with (folder / name).open(newline='') as f:
            return {r['PeriodIndex']: r for r in csv.DictReader(f) if r['PeriodIndex']}
    a = rows('ATT_By_Statistics_Interval.csv')
    b = rows('Baseline_ATT_By_Statistics_Interval.csv')
    assert a.keys() == b.keys()
    return sum((1-float(b[k]['AverageTransportTime'])/float(v['AverageTransportTime']))
               *(int(v['EndDay'])-int(v['StartDay'])+1) for k, v in a.items())


if __name__ == '__main__':
    before = hashes()
    result = pytest.main([str(ROOT / 'response_strategies/test_resilience_strategy.py'),
                          str(ROOT / 'simulation_model/tests/test_strategy_validation.py'),
                          str(ROOT / 'simulation_model/tests/test_disruptions_and_strategy.py'),
                          '-q', '-p', 'no:cacheprovider'])
    if result or '--tests-only' in sys.argv:
        assert hashes() == before
        sys.exit(result)
    from config.simulation_config import WARM_UP_DAYS, SIMULATION_DAYS, STATISTICS_INTERVAL_DAYS
    import scenario_builders
    from simulation_output_csv_writer import write_all, write_att_by_period
    from response_strategies.user_strategy import UserStrategy
    output = ROOT / 'response_strategies/benchmark_results' / ('resilience_' + dt.datetime.now().strftime('%Y%m%d_%H%M%S'))
    output.mkdir(parents=True)
    previous = output / 'previous_output'
    shutil.copytree(ROOT / 'Output', previous)
    shutil.copy2(previous / 'Baseline_ATT_By_Statistics_Interval.csv', output)
    for name in ('resilience_strategy.py', 'user_strategy.py'):
        shutil.copy2(ROOT / 'response_strategies' / name, output / name)
    context = scenario_builders.create_with_disruption()
    sim = simulation_model.Model(context, seed=2026)
    started = time.monotonic()
    print('Warm-up', WARM_UP_DAYS, flush=True)
    sim.warmup(period=dt.timedelta(days=WARM_UP_DAYS))
    periods, start_day, start_time = [], 1, sim.clock_time
    for day in range(1, SIMULATION_DAYS + 1):
        sim.run(duration=dt.timedelta(days=1))
        if day % STATISTICS_INTERVAL_DAYS == 0 or day == SIMULATION_DAYS:
            att = sim.get_teu_weighted_average_transport_time_hours(start_time, sim.clock_time) / 24
            periods.append((start_day, day, att))
            # These are partial statistics, not a resumable model checkpoint.
            write_att_by_period(output, periods)
            (output / 'progress.json').write_text(json.dumps({
                'measured_day': day, 'complete': False,
                'seconds': time.monotonic() - started,
                'fallback_errors': dict(UserStrategy.state(context).errors),
            }, indent=2))
            start_day, start_time = day + 1, sim.clock_time
            if day % 30 == 0:
                print('Day', day, 'ATT', round(att, 4), flush=True)
    write_all(sim, output)
    write_att_by_period(output, periods)
    shutil.copy2(previous / 'Baseline_ATT_By_Statistics_Interval.csv', output)
    unchanged = hashes() == before
    summary = {'loss': loss(output), 'previous_saved_loss': loss(previous),
               'mean_att': sum(p[2] for p in periods)/len(periods),
               'seconds': time.monotonic()-started, 'seed': 2026,
               'fallback_errors': dict(UserStrategy.state(context).errors),
               'protected_files_unchanged': unchanged}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2))
    (output / 'progress.json').write_text(json.dumps({'measured_day': SIMULATION_DAYS, 'complete': True}))
    print(json.dumps(summary, indent=2), str(output), flush=True)
    assert unchanged
