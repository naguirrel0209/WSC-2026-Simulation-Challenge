"""Run only static/unit checks; block Model.run and Model.warmup explicitly.

Usage from the repository root: python -B response_strategies/validate_onboard_cost.py
"""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'response_strategies/benchmark_results/onboard_cost_20260913'
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / 'o2despy')]

import simulation_model
import pytest


def _changed_protected_files(expected):
    changed = []
    for relative, digest in expected.items():
        path = ROOT / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest().upper() != digest.upper():
            changed.append(relative)
    return changed


def main():
    manifest = ARTIFACTS / 'control/protected_hashes.json'
    expected = json.loads(manifest.read_text(encoding='utf-8'))
    before = _changed_protected_files(expected)
    if before:
        print('Protected files differ from the saved control:', before)
        return 1
    output = io.StringIO()
    excluded = 'response_strategies/test_resilience_strategy.py::test_bookings_connect_and_replace_reverse_references'
    with (
        patch.object(simulation_model.Model, 'run', side_effect=AssertionError('Simulation is forbidden')) as run,
        patch.object(simulation_model.Model, 'warmup', side_effect=AssertionError('Warm-up is forbidden')) as warmup,
        contextlib.redirect_stdout(output),
        contextlib.redirect_stderr(output),
    ):
        result = pytest.main([
            str(ROOT / 'response_strategies/test_onboard_cost.py'),
            str(ROOT / 'response_strategies/test_resilience_strategy.py'),
            str(ROOT / 'simulation_model/tests/test_strategy_validation.py'),
            '--rootdir', str(ROOT), '--deselect', excluded,
            '-q', '-p', 'no:cacheprovider',
        ])
    after = _changed_protected_files(expected)
    summary = {
        'pytest_exit_code': int(result),
        'model_run_calls': run.call_count,
        'model_warmup_calls': warmup.call_count,
        'protected_files_checked': len(expected),
        'changed_protected_files': after,
        'excluded_simulation_test': excluded,
        'candidate_kpi': None,
        'strategy_sha256': hashlib.sha256(
            (ROOT / 'response_strategies/resilience_strategy.py').read_bytes()
        ).hexdigest(),
    }
    (ARTIFACTS / 'unit_tests.log').write_text(output.getvalue(), encoding='utf-8')
    (ARTIFACTS / 'validation.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(output.getvalue(), end='')
    print(json.dumps(summary, indent=2))
    return int(result) or int(bool(after or run.call_count or warmup.call_count))


if __name__ == '__main__':
    sys.exit(main())
