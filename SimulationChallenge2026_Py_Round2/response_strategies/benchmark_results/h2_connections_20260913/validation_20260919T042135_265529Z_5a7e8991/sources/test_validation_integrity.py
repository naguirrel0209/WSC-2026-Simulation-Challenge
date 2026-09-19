"""Integrity failures are exercised only on copies inside pytest's report temp."""
import json
from pathlib import Path
import shutil

import pytest
from response_strategies.validation_integrity import (
    BASELINE, CONTROL, OBSERVED, ROOT, DOCUMENTATION_RECORD, DOCUMENTATION_BEFORE,
    compare, historical_checks, snapshot,
)


@pytest.fixture
def protected_copy(tmp_path):
    expected = json.loads((ROOT / CONTROL / 'protected_hashes.json').read_text())
    paths = set(expected)
    paths.update(['AGENTS.md', DOCUMENTATION_RECORD.as_posix(), DOCUMENTATION_BEFORE.as_posix()])
    paths.update(str(p.relative_to(ROOT)) for folder in (CONTROL, OBSERVED)
                 for p in (ROOT / folder).rglob('*') if p.is_file())
    paths.update('response_strategies/' + name for name in
                 ('user_strategy.py', 'resilience_strategy.py', 'h2_control_strategy.py'))
    for relative in paths:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    return tmp_path


def test_current_observed_output_allowed_without_refreshing_control(protected_copy):
    result = historical_checks(protected_copy)
    assert result['errors'] == []
    assert result['groups']['original_protected_including_baseline']['checked'] == 156
    assert result['groups']['current_outputs_vs_observed']['checked'] == 8
    assert result['groups']['authorized_documentation']['checked'] == 1


@pytest.mark.parametrize('relative', [
    'Input/ports.csv', 'config/simulation_config.py', 'scenario_builders/disruption_scenario.py',
    'simulation_model/model.py', 'maritime_data_context/booking.py', 'main.py', BASELINE,
    'Output/Port_Waiting_Statistics.csv',
    (CONTROL / 'Output/Port_Waiting_Statistics.csv').as_posix(),
    (OBSERVED / 'Output/Port_Waiting_Statistics.csv').as_posix(),
    'response_strategies/user_strategy.py', 'response_strategies/h2_control_strategy.py',
    (CONTROL / 'protected_hashes.json').as_posix(),
    (OBSERVED / 'snapshot_hashes.json').as_posix(),
    'AGENTS.md', DOCUMENTATION_RECORD.as_posix(), DOCUMENTATION_BEFORE.as_posix(),
])
def test_each_protection_layer_rejects_tampered_copy(protected_copy, relative):
    target = protected_copy / relative
    target.write_bytes(target.read_bytes() + b'\nunauthorized change\n')
    assert historical_checks(protected_copy)['errors']


def test_before_after_detects_new_deleted_and_changed_files(tmp_path):
    (tmp_path / 'one.py').write_text('original')
    (tmp_path / 'two.py').write_text('original')
    before = snapshot(tmp_path)
    (tmp_path / 'one.py').write_text('changed')
    (tmp_path / 'two.py').unlink()
    (tmp_path / 'three.py').write_text('new')
    assert set(compare(before, snapshot(tmp_path))) == {'one.py', 'two.py', 'three.py'}


def test_missing_manifest_is_rejected(protected_copy):
    (protected_copy / CONTROL / 'protected_hashes.json').unlink()
    assert historical_checks(protected_copy)['errors'][0]['group'] == 'historical_manifests'


def test_documentation_record_cannot_exempt_motor_or_configuration(protected_copy):
    record = protected_copy / DOCUMENTATION_RECORD
    approvals = json.loads(record.read_text(encoding='utf-8-sig'))
    approvals['simulation_model/model.py'] = dict(approvals['AGENTS.md'])
    record.write_text(json.dumps(approvals), encoding='utf-8')
    assert any(e['group'] == 'documentation_record' for e in historical_checks(protected_copy)['errors'])


def test_documentation_record_cannot_refresh_previous_hash(protected_copy):
    record = protected_copy / DOCUMENTATION_RECORD
    approvals = json.loads(record.read_text(encoding='utf-8-sig'))
    approvals['AGENTS.md']['previous_sha256'] = '0' * 64
    record.write_text(json.dumps(approvals), encoding='utf-8')
    assert any(e['group'] == 'documentation_record' for e in historical_checks(protected_copy)['errors'])
