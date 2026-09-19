"""Read-only integrity checks shared by the no-advance validation runner."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY = Path('response_strategies/benchmark_results/onboard_cost_20260913')
CONTROL = HISTORY / 'control'
OBSERVED = HISTORY / 'observed_run_20260913_120119'
BASELINE = 'Output/Baseline_ATT_By_Statistics_Interval.csv'
BASE_SHA256 = 'a387c563fb91e77b7f5010e4a3f3b43ca772f4e4d58c80ab5c7be3f5245d502b'
DOCUMENTATION_RECORD = Path('response_strategies/authorized_documentation_changes.json')
DOCUMENTATION_BEFORE = Path(
    'response_strategies/benchmark_results/integrated_mechanisms_20260913/AGENTS_before.md')
AGENTS_BEFORE_SHA256 = 'db3ed0deaa544db03ab0b8e8dab3200c716fc0474775e53e946cd523e69c63cb'
MANIFEST_ANCHORS = {
    (CONTROL / 'protected_hashes.json').as_posix():
        '64c3511280f55e7a73573884483b957f0506a4b004284196548aec27a4fb09d7',
    (OBSERVED / 'snapshot_hashes.json').as_posix():
        '77a37159a9a099e879113a4dccf058d5fd4906c0def2da2c490d2af04993f048',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def compare(expected, actual):
    return {name: {'before': expected.get(name), 'after': actual.get(name)}
            for name in sorted(expected.keys() | actual.keys())
            if expected.get(name) != actual.get(name)}


def snapshot(root=ROOT, excluded=()):
    """Include untracked files and caches; ignore only environments and Git.

    The caller excludes only its own newly created report directory.
    """
    excluded = {Path(p).resolve() for p in excluded}
    result = {}
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', '.venv', 'node_modules'}
                         and (Path(current) / d).resolve() not in excluded)
        for name in sorted(files):
            path = Path(current) / name
            if path.is_symlink():
                continue
            result[path.relative_to(root).as_posix()] = digest(path)
    return result


def historical_checks(root=ROOT):
    """Never refresh historical hashes. A mismatching input remains a failure."""
    anchors = compare(MANIFEST_ANCHORS, {p: digest(root / p) for p in MANIFEST_ANCHORS})
    if anchors:
        return {'groups': {}, 'documentation': {},
                'errors': [{'group': 'historical_manifests', 'differences': anchors}]}
    expected = {p: h.lower() for p, h in
                read_json(root / CONTROL / 'protected_hashes.json').items()}
    archived = {p: h.lower() for p, h in
                read_json(root / OBSERVED / 'snapshot_hashes.json').items()}
    strict = {p: h for p, h in expected.items()
              if not p.startswith('Output/') or p == BASELINE}
    generated = {p: h for p, h in expected.items() if p.startswith('Output/')}
    current_csv = {p: h for p, h in archived.items() if p.startswith('Output/')}
    errors = []

    def verify(label, base, values):
        differences = compare(values, {p: digest(base / p) for p in values})
        if differences:
            errors.append({'group': label, 'differences': differences})
        return {'checked': len(values), 'differences': differences}

    groups = {
        'original_protected_including_baseline': verify('protected', root, strict),
        'control_outputs': verify('control_outputs', root / CONTROL, generated),
        'observed_archive': verify('observed_archive', root / OBSERVED, archived),
        'current_outputs_vs_observed': verify('current_outputs', root, current_csv),
    }
    if len(generated) != 8 or generated.keys() != current_csv.keys():
        errors.append({'group': 'output_inventory', 'error': 'Expected the same eight CSVs'})
    for label, folder in [('current', root / 'Output'),
                          ('control', root / CONTROL / 'Output'),
                          ('observed', root / OBSERVED / 'Output')]:
        names = {'Output/' + p.name for p in folder.glob('*.csv')}
        if names != generated.keys():
            errors.append({'group': label + '_csv_inventory', 'actual': sorted(names)})
    groups['control_source'] = verify('control_source', root / CONTROL,
                                        {'resilience_strategy.py': BASE_SHA256})
    groups['candidate_base'] = verify('candidate_base', root / 'response_strategies',
                                         {'h2_control_strategy.py': BASE_SHA256})
    groups['active_H1'] = verify('active_H1', root / 'response_strategies',
                                {p: archived[p] for p in
                                 ('user_strategy.py', 'resilience_strategy.py')})
    # AGENTS.md was added after the original control manifest. Its explicitly
    # authorized update is an ADDITIONAL check, never an exemption from strict.
    documentation = {p: {'control': h, 'current': digest(root / p)}
                     for p, h in expected.items() if p.endswith('.md')}
    try:
        approvals = read_json(root / DOCUMENTATION_RECORD)
        if set(approvals) != {'AGENTS.md'}:
            raise ValueError('Only the expressly authorized root AGENTS.md may be recorded')
        approval = approvals['AGENTS.md']
        if approval['previous_sha256'] != AGENTS_BEFORE_SHA256:
            raise ValueError('Original AGENTS.md hash must not be refreshed')
        groups['documentation_original'] = verify('documentation_original', root,
            {DOCUMENTATION_BEFORE.as_posix(): AGENTS_BEFORE_SHA256})
        groups['authorized_documentation'] = verify('authorized_documentation', root,
            {'AGENTS.md': approval['authorized_sha256']})
        documentation['AGENTS.md'] = {
            'control': expected.get('AGENTS.md'), 'before_task': AGENTS_BEFORE_SHA256,
            'current': digest(root / 'AGENTS.md'), 'authorization': approval,
        }
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append({'group': 'documentation_record', 'error': str(error)})
    return {'groups': groups, 'documentation': documentation, 'errors': errors}
