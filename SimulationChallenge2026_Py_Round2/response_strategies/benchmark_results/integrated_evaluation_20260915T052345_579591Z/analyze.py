"""Analyze only completed archived CSVs and passive observations; no model imports."""
import csv
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys

FOLDER = Path(__file__).resolve().parent
WINDOWS = [(41,100),(141,200),(216,240),(261,275),(276,320),(321,330),(331,360),(261,360)]
def load(name):
    return json.loads((FOLDER / name).read_text(encoding='utf-8-sig'))
def save(name, value):
    (FOLDER / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))
def number(value):
    return float(value.replace(',', '').replace('%', ''))
def intervals(path):
    result = {(int(r['StartDay']),int(r['EndDay'])): number(r['AverageTransportTime'])
              for r in rows(path) if r['PeriodIndex'].isdigit()}
    assert list(result) == [(d,d+4) for d in range(1,361,5)]
    assert all(v > 0 for v in result.values())
    return result
def metrics(path):
    att = intervals(path/'ATT_By_Statistics_Interval.csv')
    base = intervals(path/'Baseline_ATT_By_Statistics_Interval.csv')
    loss = {k:(1-base[k]/v)*5 for k,v in att.items()}
    result = {'mean_interval_att_days':statistics.mean(att.values()), 'loss_kpi':sum(loss.values()),
              'baseline_mean_days':statistics.mean(base.values()),
              'intervals':[{'start':a,'end':b,'att':att[a,b],'loss':loss[a,b]} for a,b in att],
              'windows':{}}
    for a,b in WINDOWS:
        keys = [k for k in att if a <= k[0] and k[1] <= b]
        result['windows'][f'{a}-{b}'] = {'att':statistics.mean(att[k] for k in keys),
                                        'loss':sum(loss[k] for k in keys)}
    for filename,key,label,excluded in [
        ('Port_Waiting_Statistics.csv','Port','ports',{'Port'}),
        ('Service_Route_Utilization.csv','Route','routes',{'Route','Name'}),
        ('Average_Vessel_State_Counts.csv','Metric','vessels',{'Metric'})]:
        result[label] = {r[key]:{k:number(v) for k,v in r.items() if k not in excluded}
                         for r in rows(path/filename)}
    result['od'] = {}
    for filename in ('Average_Origin_Waiting_TEU_By_OD.csv','Average_In_Transit_TEU_By_OD.csv',
                     'Cumulative_Completed_TEU_By_OD.csv'):
        result['od'][filename] = {r[next(iter(r))]+' -> '+k:number(v)
            for r in rows(path/filename) for k,v in r.items()
            if k != next(iter(r)) and v != '-'}
    result['completed_teu_rounded_sum'] = sum(result['od']['Cumulative_Completed_TEU_By_OD.csv'].values())
    return result

def main():
    run = load('run.json')
    if not run['complete'] or run['measured_days_completed'] != 360:
        raise RuntimeError('Only a completed run may be evaluated.')
    assert len(list((FOLDER/'Output').glob('*.csv'))) == 8
    for filename, expected in run['output_hashes'].items():
        assert hashlib.sha256((FOLDER/'Output'/filename).read_bytes()).hexdigest() == expected
    assert (FOLDER/'Output/Baseline_ATT_By_Statistics_Interval.csv').read_bytes() == (
        FOLDER/'H1_control_Output/Baseline_ATT_By_Statistics_Interval.csv').read_bytes()
    control, candidate = metrics(FOLDER/'H1_control_Output'), metrics(FOLDER/'Output')
    report = {'control':control, 'integrated':candidate, 'comparison_control':'H1',
              'complete':True, 'individual_mechanism_attribution':False}
    for metric in ('mean_interval_att_days','loss_kpi','completed_teu_rounded_sum'):
        old,new = control[metric],candidate[metric]
        report[metric+'_change'] = {'absolute':new-old,'percent':100*(new/old-1)}
    report['interval_changes'] = [{'start':old['start'],'end':old['end'],
        'att':new['att']-old['att'],'loss':new['loss']-old['loss']}
        for old,new in zip(control['intervals'], candidate['intervals'])]
    report['window_changes'] = {key:{m:candidate['windows'][key][m]-old
        for m,old in vals.items()} for key,vals in control['windows'].items()}
    for group in ('ports','routes','vessels'):
        report[group+'_changes'] = {
            key:{m:candidate[group].get(key,{}).get(m,0)-v for m,v in vals.items()}
            for key,vals in control[group].items()}
    report['new_routes'] = {k:v for k,v in candidate['routes'].items() if k not in control['routes']}
    report['od_largest_changes'] = {}
    for name, values in control['od'].items():
        deltas = [{'od':k,'control':v,'integrated':candidate['od'][name][k],
                   'delta':candidate['od'][name][k]-v} for k,v in values.items()]
        report['od_largest_changes'][name] = {
            'increases':sorted(deltas,key=lambda r:-r['delta'])[:10],
            'decreases':sorted(deltas,key=lambda r:r['delta'])[:10]}
    obs = load('observation_summary.json')
    with (FOLDER/'daily_observations.jsonl').open(encoding='utf-8') as f:
        samples = [json.loads(line) for line in f]
    assert [r['day'] for r in samples] == list(range(361))
    anomalies = []
    for sample in samples:
        if len(sample['vessels']) != 41 or len({v['id'] for v in sample['vessels']}) != 41:
            anomalies.append({'day':sample['day'],'error':'vessel identity count'})
        for v in sample['vessels']:
            reasons = []
            if len(v['states']) != 1: reasons.append('state membership count')
            if not v['registered']: reasons.append('route registration')
            if not v['cargo_references_valid']: reasons.append('cargo vessel reference')
            if v['cargo_teu'] > v['capacity_teu'] or v['cargo_teu'] < 0: reasons.append('cargo capacity')
            if reasons: anomalies.append({'day':sample['day'],'vessel':v['id'],'reasons':reasons,'data':v})
    report['observations'] = {
        **obs, 'daily_samples':len(samples), 'vessel_audit_anomaly_count':len(anomalies),
        'vessel_audit_anomaly_examples':anomalies[:100], 'final_state':samples[-1],
        'sampled_total_queue_peak':max(
            ({'day':r['day'],'teu':sum(p['total'] for p in r['ports'])} for r in samples),
            key=lambda r:r['teu']),
        'raw_storage_list_age_sample_not_valid_as_pending_age':max(
            ({'day':r['day'],'port':p['port'],'age_days':p['max_stored_shipment_age_days']}
             for r in samples for p in r['ports']),key=lambda r:r['age_days']),
        'any_alternative_routes_sampled':any(r['source'] is not None for s in samples for r in s['routes'])}
    report['observation_quality_notes'] = ['The raw stored-shipment age field includes completed shipments retained in port storage lists. Do not interpret it as pending shipment age or local waiting time. Queue TEU values and maxima use dedicated model counters and are unaffected.', 'The historical H1 run lacks matching peak and vessel telemetry. No H1 instrumented replay was performed.', 'No same-process decision cost decomposition was recorded; the combination cannot identify the causal contribution of each mechanism.']
    report['alternative_route_audit'] = load('alternative_route_audit.json')
    report['integrity'] = {'changes_outside_experiment':run['changes_outside_experiment'],
                          'historical_checks_after_errors':load('historical_checks_after.json')['errors']}
    save('comparison.json',report)
    with (FOLDER/'interval_comparison.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['StartDay','EndDay','H1_ATT','Integrated_ATT','ATT_change','H1_loss','Integrated_loss','Loss_change'])
        for old,new,change in zip(control['intervals'],candidate['intervals'],report['interval_changes']):
            w.writerow([old['start'],old['end'],old['att'],new['att'],change['att'],old['loss'],new['loss'],change['loss']])
    compact = {
        'control':{k:control[k] for k in ('mean_interval_att_days','loss_kpi','completed_teu_rounded_sum')},
        'integrated':{k:candidate[k] for k in ('mean_interval_att_days','loss_kpi','completed_teu_rounded_sum')},
        'att_change':report['mean_interval_att_days_change'], 'loss_change':report['loss_kpi_change'],
        'windows':report['window_changes'], 'ports':candidate['ports'], 'port_changes':report['ports_changes'],
        'route_changes':report['routes_changes'], 'new_routes':report['new_routes'],
        'largest_interval_regressions':sorted(report['interval_changes'],key=lambda r:-r['att'])[:8],
        'largest_interval_improvements':sorted(report['interval_changes'],key=lambda r:r['att'])[:8],
        'strategy_errors':obs['strategy_errors'],'audit_anomalies':len(anomalies),
        'same_41_vessel_objects':obs['same_41_vessel_objects'],'same_leg_objects':obs['same_leg_objects'],
        'queue_peak':report['observations']['sampled_total_queue_peak'],
        'integrity':report['integrity']}
    print(json.dumps(compact,indent=2))
if __name__=='__main__':
    main()
