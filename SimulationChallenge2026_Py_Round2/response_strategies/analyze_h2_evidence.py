"""Read the eight archived CSVs per run and recompute comparable evidence.

No simulation imports. Each execution creates a fresh analysis folder.
"""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import statistics
import uuid

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'response_strategies/benchmark_results/onboard_cost_20260913'
DEST = ROOT / 'response_strategies/benchmark_results/h2_connections_20260913'
WINDOWS = [(41, 100), (141, 200), (216, 240), (261, 275), (276, 320),
           (321, 330), (331, 360), (261, 360)]


def number(value):
    return float(value.replace(',', '').replace('%', ''))


def rows(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def intervals(raw):
    result = {}
    for row in raw:
        if not row['PeriodIndex'].isdigit():
            continue
        key = int(row['StartDay']), int(row['EndDay'])
        if key in result:
            raise ValueError('Duplicate interval')
        result[key] = number(row['AverageTransportTime'])
    if list(result) != [(day, day + 4) for day in range(1, 361, 5)]:
        raise ValueError('Expected exactly 72 consecutive five-day intervals')
    if any(value <= 0 for value in result.values()):
        raise ValueError('ATT must be positive')
    return result


def summarize(folder):
    tables = {file.name: rows(file) for file in sorted((folder / 'Output').glob('*.csv'))}
    if len(tables) != 8:
        raise ValueError('Expected eight archived CSVs')
    att = intervals(tables['ATT_By_Statistics_Interval.csv'])
    baseline = intervals(tables['Baseline_ATT_By_Statistics_Interval.csv'])
    loss = {key: (1 - baseline[key] / value) * (key[1] - key[0] + 1)
            for key, value in att.items()}
    recorded = json.loads((folder / 'metrics.json').read_text(encoding='utf-8-sig'))
    mean, kpi = statistics.mean(att.values()), sum(loss.values())
    assert abs(mean - recorded['mean_interval_att_days']) < 1e-10
    assert abs(kpi - recorded['loss_kpi']) < 1e-10
    result = {
        'source': str(folder.relative_to(ROOT)),
        'hashes': {name: hashlib.sha256((folder / 'Output' / name).read_bytes()).hexdigest()
                   for name in tables},
        'rows_read': {name: len(data) for name, data in tables.items()},
        'att_mean_days': mean, 'loss_kpi': kpi,
        'baseline_att_mean_days': statistics.mean(baseline.values()),
        'archived_metrics_reconciled': True,
        'windows': {},
        'intervals': [{'days': f'{a}-{b}', 'att_days': att[a, b], 'loss_kpi': loss[a, b]}
                      for a, b in att],
    }
    for start, end in WINDOWS:
        selected = [key for key in att if start <= key[0] and key[1] <= end]
        result['windows'][f'{start}-{end}'] = {
            'att_mean_days': statistics.mean(att[key] for key in selected),
            'loss_kpi': sum(loss[key] for key in selected), 'subtotal': (start, end) == (261, 360),
        }
    for name, key, label, text_columns in [
        ('Port_Waiting_Statistics.csv', 'Port', 'ports', {'Port'}),
        ('Service_Route_Utilization.csv', 'Route', 'routes', {'Route', 'Name'}),
        ('Average_Vessel_State_Counts.csv', 'Metric', 'vessels', {'Metric'}),
    ]:
        result[label] = {row[key]: {k: number(v) for k, v in row.items() if k not in text_columns}
                         for row in tables[name]}
    result['od'] = {}
    for name in ('Average_Origin_Waiting_TEU_By_OD.csv', 'Average_In_Transit_TEU_By_OD.csv',
                 'Cumulative_Completed_TEU_By_OD.csv'):
        matrix = {}
        for row in tables[name]:
            origin_key = next(iter(row))
            for destination, value in row.items():
                if destination == origin_key or value == '-':
                    continue
                matrix[row[origin_key] + ' -> ' + destination] = number(value)
        result['od'][name] = {'rounded_cell_sum': sum(matrix.values()), 'cells': matrix}
    return result


def main():
    control = summarize(BASE / 'control')
    observed = summarize(BASE / 'observed_run_20260913_120119')
    comparison = {'control': control, 'observed_consistent_with_H1': observed,
                  'candidate_h2_kpi': None, 'simulation_executed': False}
    for group in ('ports', 'routes', 'vessels'):
        comparison[group + '_deltas'] = {
            key: {metric: observed[group][key][metric] - value for metric, value in values.items()}
            for key, values in control[group].items()}
    comparison['interval_deltas'] = [
        {'days': old['days'], 'att_days': new['att_days'] - old['att_days'],
         'loss_kpi': new['loss_kpi'] - old['loss_kpi']}
        for old, new in zip(control['intervals'], observed['intervals'])]
    comparison['od_largest_increases'] = {}
    for name in control['od']:
        changes = [{'od': key, 'control': value, 'observed': observed['od'][name]['cells'][key],
                    'delta': observed['od'][name]['cells'][key] - value}
                   for key, value in control['od'][name]['cells'].items()]
        comparison['od_largest_increases'][name] = sorted(changes, key=lambda row: -row['delta'])[:10]
    comparison['port_services'] = {}
    for row in rows(ROOT / 'Input/route_segments.csv'):
        for port in (row['FromPort'], row['ToPort']):
            comparison['port_services'].setdefault(port, set()).add(row['RouteId'])
    comparison['port_services'] = {p: sorted(r) for p, r in comparison['port_services'].items()}
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder = DEST / ('analysis_' + stamp + '_' + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    (folder / 'evidence.json').write_text(json.dumps(comparison, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(folder), 'control_att': control['att_mean_days'],
                      'observed_att': observed['att_mean_days'],
                      'control_kpi': control['loss_kpi'], 'observed_kpi': observed['loss_kpi'],
                      'largest_port_increases': sorted(comparison['ports_deltas'].items(),
                              key=lambda row: -row[1]['Total Waiting TEU'])[:5],
                      'od_increases': comparison['od_largest_increases']}, indent=2))


if __name__ == '__main__':
    main()
