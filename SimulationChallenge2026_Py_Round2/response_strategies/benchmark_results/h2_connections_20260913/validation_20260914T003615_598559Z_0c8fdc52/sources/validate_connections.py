"""Validate H1 and isolated H2 with all public model advance methods blocked."""
import contextlib
import datetime as dt
import io
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / 'o2despy')]
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'

from response_strategies.validation_integrity import (
    compare, digest, historical_checks, snapshot,
)

EXCLUDED = ('response_strategies/test_resilience_strategy.py::'
            'test_bookings_connect_and_replace_reverse_references')
TESTS = [
    'response_strategies/test_onboard_cost.py',
    'response_strategies/test_resilience_strategy.py',
    'response_strategies/test_h2_connections.py',
    'response_strategies/test_validation_integrity.py',
    'simulation_model/tests/test_strategy_validation.py',
]


def save(folder, name, value):
    (folder / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n',
                               encoding='utf-8')


def main():
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder = ROOT / 'response_strategies/benchmark_results/h2_connections_20260913' / (
        'validation_' + stamp + '_' + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    before = snapshot(excluded=[folder])
    save(folder, 'before_hashes.json', before)
    try:
        checks = historical_checks()
    except Exception:
        checks = {'errors': [{'group': 'manifest_read', 'error': traceback.format_exc()}]}
    save(folder, 'historical_checks.json', checks)
    source_names = ('user_strategy.py', 'resilience_strategy.py', 'h2_control_strategy.py',
                    'h2_connection_strategy.py', 'H2_HYPOTHESIS.md',
                    'validate_onboard_cost.py', 'validate_connections.py',
                    'validation_integrity.py', 'test_h2_connections.py',
                    'test_validation_integrity.py')
    (folder / 'sources').mkdir()
    for name in source_names:
        source = ROOT / 'response_strategies' / name
        if source.is_file():
            shutil.copyfile(source, folder / 'sources' / name)
    args = TESTS + ['--rootdir', str(ROOT), '--deselect', EXCLUDED,
                    '--basetemp', str(folder / 'tmp'), '-q', '-p', 'no:cacheprovider']
    summary = {'started_utc': stamp, 'python': sys.executable,
               'python_version': sys.version, 'bytecode_disabled': sys.dont_write_bytecode,
               'pytest_arguments': args, 'excluded_simulation_test': EXCLUDED,
               'candidate_kpi': None, 'simulation_executed': False,
               'pytest_exit_code': None, 'calls_blocked': {},
               'historical_errors': checks['errors']}
    capture = io.StringIO()
    guards = {}
    try:
        if checks['errors']:
            raise RuntimeError('Historical integrity check failed; tests were not started')
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(capture))
            stack.enter_context(contextlib.redirect_stderr(capture))
            # Base methods are blocked before importing tests, including APIs
            # that could advance a child activity without calling Model.run.
            from o2des.core import Sandbox
            for method in ('run', 'warmup', 'run_once', 'run_all', 'run_until',
                           'run_for_period', 'run_multiple_times', 'run_at_speed',
                           'warmup_until', 'warmup_for_period'):
                guards['Sandbox.' + method] = stack.enter_context(patch.object(
                    Sandbox, method, side_effect=AssertionError('Model advancement forbidden')))
            import simulation_model
            for method in ('run', 'warmup'):
                guards['Model.' + method] = stack.enter_context(patch.object(
                    simulation_model.Model, method,
                    side_effect=AssertionError('Simulation and warm-up are forbidden')))
            import pytest
            summary['pytest_exit_code'] = int(pytest.main(args))
    except BaseException:
        summary['error'] = traceback.format_exc()
        capture.write(summary['error'])
    finally:
        summary['calls_blocked'] = {key: value.call_count for key, value in guards.items()}
        summary['model_run_calls'] = summary['calls_blocked'].get('Model.run', 0)
        summary['model_warmup_calls'] = summary['calls_blocked'].get('Model.warmup', 0)
        after = snapshot(excluded=[folder])
        save(folder, 'after_hashes.json', after)
        summary['files_checked_before_tests'] = len(before)
        summary['changed_during_tests'] = compare(before, after)
        summary['passed'] = (summary['pytest_exit_code'] == 0 and not checks['errors']
                             and not summary['changed_during_tests']
                             and not any(summary['calls_blocked'].values())
                             and 'error' not in summary)
        summary['source_sha256'] = {name: digest(folder / 'sources' / name)
                                    for name in source_names}
        (folder / 'unit_tests.log').write_text(capture.getvalue(), encoding='utf-8')
        save(folder, 'validation.json', summary)
    print(capture.getvalue(), end='')
    print(json.dumps({'passed': summary['passed'], 'report': str(folder),
                      'calls_blocked': summary['calls_blocked'],
                      'changed_during_tests': summary['changed_during_tests']}, indent=2))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
