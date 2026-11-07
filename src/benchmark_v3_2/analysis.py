"""Paired, frame-level analyses of frozen v3.2 predictions; never fits models."""
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

MODELS = ('LR', 'RF', 'ModernBERT')
CONDITIONS = ('C0', 'C1', 'C4', 'C5', 'C6')
FIELDS = ['analysis_id', 'hypothesis', 'N_frames', 'N_rows', 'model', 'condition',
          'effect_size', 'CI', 'raw_p', 'adjusted_p', 'confirmatory_or_exploratory', 'notes']


def _record(name, model, condition, n, *, effect=np.nan, notes='', **extra):
    return dict(analysis_id=name, hypothesis=name, N_frames=n, N_rows=n,
                model=model, condition=condition, effect_size=effect, CI='',
                raw_p=np.nan, adjusted_p=np.nan,
                confirmatory_or_exploratory='exploratory', notes=notes, **extra)


def _interval(values, rng, replicates):
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        return '', np.nan, np.nan
    means = np.array([rng.choice(values, len(values), replace=True).mean()
                      for _ in range(replicates)])
    lo, hi = np.quantile(means, [.025, .975])
    return f'[{lo:.10g}, {hi:.10g}]', float(lo), float(hi)


def _holm(rows):
    valid = sorted((i for i, r in enumerate(rows) if pd.notna(r['raw_p'])),
                   key=lambda i: rows[i]['raw_p'])
    last = 0.
    # Keep all 24 preregistered hypotheses in the family, even when unsupported.
    for rank, i in enumerate(valid):
        last = max(last, min(1., (len(rows) - rank) * rows[i]['raw_p']))
        rows[i]['adjusted_p'] = last


def _metrics(data, model, condition, cohort):
    n = len(data)
    positive = data[data.true_label == 1]
    negative = data[data.true_label == 0]
    recall = float(positive.prediction.mean()) if len(positive) else np.nan
    fpr = float(negative.prediction.mean()) if len(negative) else np.nan
    accuracy = float((data.prediction == data.true_label).mean()) if n else np.nan
    return _record(f'{cohort}_performance', model, condition, n, effect=accuracy,
                   notes='Combined accuracy is secondary to class-separated metrics; undefined denominators are blank.',
                   recall=recall, false_positive_rate=fpr, specificity=1-fpr,
                   false_negative_rate=1-recall, accuracy=accuracy,
                   N_positive=len(positive), N_negative=len(negative), cohort=cohort)


def _available_slope(pairs, model, label, rng, replicates):
    repeated = pd.concat([pairs[model, condition] for condition in CONDITIONS[1:]], ignore_index=True)
    repeated = repeated[repeated.true_label == label].copy()
    slopes, n_rows = [], 0
    if 'surface_distance' in repeated:
        repeated['movement'] = (repeated.C0_probability - repeated.probability).abs()
        for _, frame in repeated.groupby('frame_id', sort=True):
            frame = frame[['surface_distance', 'movement']].dropna()
            if len(frame) >= 2 and frame.surface_distance.nunique() > 1:
                x, y = frame.surface_distance.to_numpy(dtype=float), frame.movement.to_numpy(dtype=float)
                slopes.append(float(np.dot(x-x.mean(), y-y.mean()) / np.dot(x-x.mean(), x-x.mean())))
                n_rows += len(frame)
    row = _record('available_pair_mean_frame_distance_absolute_movement_slope', model, 'C1/C4/C5/C6', len(slopes),
        effect=float(np.mean(slopes)) if slopes else np.nan, true_label=label, cohort='available_pair',
        notes='Secondary conditional available-pair summary, separate from primary. Each frame needs at least two approved rewrites with distance variation. Mean within-frame slope, bootstrap whole frames. Selected missingness prevents causal interpretation; unsupported quantities blank.')
    row['N_rows'] = n_rows
    row['CI'], row['ci_lower'], row['ci_upper'] = _interval(slopes, rng, replicates)
    row.update(bootstrap_replicates=replicates, bootstrap_unit='frame')
    return row


def _write(path, content):
    payload = content.encode('utf-8')
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError(f'Refusing to overwrite different output: {path}')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(payload)


def _table(output, folder, name, records):
    table = pd.DataFrame(records)
    for field in FIELDS:
        if field not in table:
            table[field] = pd.Series(dtype='object')
    table = table[FIELDS + [c for c in table if c not in FIELDS]]
    _write(output / folder / f'{name}.csv', table.to_csv(index=False, na_rep='', lineterminator='\n'))
    shown = table.fillna('').astype(str)
    escape = lambda value: value.replace('|', '\\|').replace('\n', ' ')
    lines = ['| ' + ' | '.join(shown.columns) + ' |', '| ' + ' | '.join(['---'] * len(shown.columns)) + ' |']
    lines += ['| ' + ' | '.join(escape(v) for v in row) + ' |' for row in shown.itertuples(index=False, name=None)]
    _write(output / folder / f'{name}.md', '\n'.join(lines) + '\n')


def analyze(matrix_path, predictions_dir, output_dir, *, bootstrap_replicates=2000, seed=42):
    """Analyze frozen inputs, writing only new or byte-identical artifacts.

    Primary cohort requires the matrix complete-case flag and all five conditions
    in every model. Available pairs are calculated separately per model/condition.
    Signed probability change is P(C0)-P(condition), without causal interpretation.
    """
    if bootstrap_replicates < 1:
        raise ValueError('bootstrap_replicates must be positive')
    matrix = pd.read_csv(matrix_path, dtype={'frame_id': str})
    keys = ['frame_id', 'condition']
    if matrix.duplicated(keys).any():
        raise ValueError('Duplicate matrix frame/condition')
    if not matrix.true_label.isin([0, 1]).all():
        raise ValueError('Labels must be binary')
    flag = matrix.primary_complete_case.astype(str).str.lower().isin(['true', '1'])
    flagged = flag.groupby(matrix.frame_id).all()
    eligible = set(flagged[flagged].index)
    frames = {}
    for model in MODELS:
        predictions = pd.read_csv(Path(predictions_dir) / f'{model}_predictions.csv', dtype={'frame_id': str})
        if predictions.duplicated(keys).any():
            raise ValueError('Duplicate prediction frame/condition')
        if not predictions.prediction.isin([0, 1]).all() or not predictions.probability.between(0, 1).all():
            raise ValueError('Invalid predictions')
        data = matrix.merge(predictions[keys + ['true_label', 'probability', 'prediction']], on=keys,
                            suffixes=('', '_prediction'), validate='one_to_one')
        if not (data.true_label == data.true_label_prediction).all():
            raise ValueError('Prediction labels disagree with matrix')
        if data.groupby('frame_id').true_label.nunique().gt(1).any():
            raise ValueError('Frame labels vary across conditions')
        frames[model] = data
        complete = data[data.condition.isin(CONDITIONS)].groupby('frame_id').condition.nunique()
        eligible &= set(complete[complete == len(CONDITIONS)].index)
    rng = np.random.default_rng(seed)
    primary, available, transitions, tests, intervals, effects, associations, secondary = ([] for _ in range(8))
    pairs = {}
    available_pairs = {}
    available_effects, available_slopes, available_transitions = [], [], []
    for model, data in frames.items():
        baseline = data[data.condition == 'C0'][['frame_id', 'prediction', 'probability']].rename(
            columns={'prediction': 'C0_prediction', 'probability': 'C0_probability'})
        for condition in CONDITIONS:
            pair = data[data.condition == condition].merge(baseline, on='frame_id', validate='one_to_one')
            complete = pair[pair.frame_id.isin(eligible)].copy()
            pairs[model, condition] = complete
            available_pairs[model, condition] = pair
            primary.append(_metrics(complete, model, condition, 'primary'))
            available.append(_metrics(pair, model, condition, 'available_pair'))
            if condition == 'C0':
                continue
            available_neg = pair[pair.true_label == 0]
            available_transitions.append(_record('available_pair_negative_threshold_transitions', model, condition, len(available_neg),
                cohort='available_pair', notes='Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort.',
                existing_false_positives=int((available_neg.C0_prediction == 1).sum()),
                persistent_false_positives=int(((available_neg.C0_prediction == 1) & (available_neg.prediction == 1)).sum()),
                new_false_positives=int(((available_neg.C0_prediction == 0) & (available_neg.prediction == 1)).sum()),
                recoveries=int(((available_neg.C0_prediction == 1) & (available_neg.prediction == 0)).sum())))
            for label in (0, 1):
                group = pair[pair.true_label == label]
                delta = group.C0_probability - group.probability
                row = _record('available_pair_probability_effects', model, condition, len(group),
                    effect=float(delta.mean()) if len(delta) else np.nan, true_label=label, cohort='available_pair',
                    mean_signed_delta=float(delta.mean()) if len(delta) else np.nan,
                    mean_absolute_delta=float(delta.abs().mean()) if len(delta) else np.nan,
                    notes='Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation.')
                row['CI'], row['signed_ci_lower'], row['signed_ci_upper'] = _interval(delta, rng, bootstrap_replicates)
                row['absolute_delta_CI'], row['absolute_ci_lower'], row['absolute_ci_upper'] = _interval(delta.abs(), rng, bootstrap_replicates)
                row.update(bootstrap_unit='frame', bootstrap_replicates=bootstrap_replicates, seed=seed)
                available_effects.append(row)
            neg = complete[complete.true_label == 0]
            transitions.append(_record('negative_threshold_transitions', model, condition, len(neg),
                existing_false_positives=int((neg.C0_prediction == 1).sum()),
                persistent_false_positives=int(((neg.C0_prediction == 1) & (neg.prediction == 1)).sum()),
                new_false_positives=int(((neg.C0_prediction == 0) & (neg.prediction == 1)).sum()),
                recoveries=int(((neg.C0_prediction == 1) & (neg.prediction == 0)).sum())))
            for label in (0, 1):
                group = complete[complete.true_label == label]
                change = group.prediction.to_numpy() - group.C0_prediction.to_numpy()
                b, c = int((change == 1).sum()), int((change == -1).sum())
                p = float(binomtest(b, b+c, .5).pvalue) if b+c else (1. if len(group) else np.nan)
                row = _record('paired_class_prediction_rate', model, condition, len(group),
                    effect=float(change.mean()) if len(group) else np.nan,
                    true_label=label, baseline_to_positive=b, baseline_to_negative=c,
                    notes='Exact two-sided McNemar; effect is condition minus C0 FPR (label 0) or recall (label 1). No support: undefined.')
                row.update(raw_p=p)
                row['CI'], lo, hi = _interval(change, rng, bootstrap_replicates)
                tests.append(row)
                intervals.append(dict(row, ci_lower=lo, ci_upper=hi, bootstrap_replicates=bootstrap_replicates,
                                      bootstrap_unit='frame', seed=seed))
            for label in (0, 1):
                group = complete[complete.true_label == label]
                delta = group.C0_probability - group.probability
                effect = _record('mean_signed_probability_delta', model, condition, len(group),
                    effect=float(delta.mean()) if len(delta) else np.nan, true_label=label,
                    mean_signed_delta=float(delta.mean()) if len(delta) else np.nan,
                    mean_absolute_delta=float(delta.abs().mean()) if len(delta) else np.nan,
                    notes='Class-separated probability effect; signed P0-Pi and absolute movement; no causal interpretation.')
                effect['CI'], lo, hi = _interval(delta, rng, bootstrap_replicates)
                intervals.append(dict(effect, ci_lower=lo, ci_upper=hi, bootstrap_replicates=bootstrap_replicates,
                                      bootstrap_unit='frame', seed=seed))
                absolute = dict(effect, analysis_id='mean_absolute_probability_delta',
                                hypothesis='mean_absolute_probability_delta', effect_size=effect['mean_absolute_delta'])
                absolute['CI'], lo, hi = _interval(delta.abs(), rng, bootstrap_replicates)
                effect['absolute_delta_CI'] = absolute['CI']
                effects.append(effect)
                intervals.append(dict(absolute, ci_lower=lo, ci_upper=hi, bootstrap_replicates=bootstrap_replicates,
                                      bootstrap_unit='frame', seed=seed))
        for label in (0, 1):
            repeated = pd.concat([pairs[model, condition] for condition in CONDITIONS[1:]], ignore_index=True)
            repeated = repeated[repeated.true_label == label].copy()
            slopes = []
            supported_rows = 0
            if 'surface_distance' in repeated:
                repeated['movement'] = (repeated.C0_probability - repeated.probability).abs()
                for _, frame in repeated.groupby('frame_id', sort=True):
                    frame = frame[['surface_distance', 'movement']].dropna()
                    if len(frame) >= 2 and frame.surface_distance.nunique() > 1:
                        x = frame.surface_distance.to_numpy(dtype=float)
                        y = frame.movement.to_numpy(dtype=float)
                        slopes.append(float(np.dot(x-x.mean(), y-y.mean()) / np.dot(x-x.mean(), x-x.mean())))
                        supported_rows += len(frame)
            row = _record('mean_frame_distance_absolute_movement_slope', model, 'C1/C4/C5/C6', len(slopes),
                effect=float(np.mean(slopes)) if slopes else np.nan, true_label=label,
                notes='Mean within-frame slope across four rewrites, restricted to frames with distance variation; frame bootstrap; missingness prevents causal interpretation. No usable slopes: undefined.')
            row['N_rows'] = supported_rows
            row['CI'], lo, hi = _interval(slopes, rng, bootstrap_replicates)
            associations.append(row)
            intervals.append(dict(row, ci_lower=lo, ci_upper=hi, bootstrap_replicates=bootstrap_replicates,
                                  bootstrap_unit='frame', seed=seed))
    _holm(tests)
    for model in MODELS:
        for label in (0, 1):
            row = _available_slope(available_pairs, model, label, rng, bootstrap_replicates)
            row['seed'] = seed
            available_slopes.append(row)
    for first, second in combinations(MODELS, 2):
        for condition in CONDITIONS[1:]:
            left, right = pairs[first, condition], pairs[second, condition]
            matched = left.merge(right, on='frame_id', suffixes=('_a', '_b'), validate='one_to_one')
            for label in (0, 1):
                group = matched[matched.true_label_a == label]
                delta = ((group.C0_probability_a - group.probability_a).abs() -
                         (group.C0_probability_b - group.probability_b).abs())
                row = _record('paired_model_absolute_movement_difference', f'{first}-{second}', condition, len(group),
                    effect=float(delta.mean()) if len(delta) else np.nan, true_label=label,
                    notes='Exploratory paired absolute movement difference, first minus second model; frame bootstrap. Raw p is an exact two-sided sign test excluding ties; secondary 24-test Holm family; no causal interpretation.')
                nonzero = delta[~np.isclose(delta, 0)]
                row['raw_p'] = float(binomtest(int((nonzero > 0).sum()), len(nonzero)).pvalue) if len(nonzero) else (1. if len(delta) else np.nan)
                row['CI'], lo, hi = _interval(delta, rng, bootstrap_replicates)
                secondary.append(row)
                intervals.append(dict(row, ci_lower=lo, ci_upper=hi, bootstrap_replicates=bootstrap_replicates,
                                      bootstrap_unit='frame', seed=seed))
    _holm(secondary)
    wide = []
    for condition in CONDITIONS:
        row = _record('primary_condition_performance', 'LR/RF/ModernBERT', condition, len(eligible),
                      notes='Primary complete cohort. Recall/FNR and FPR/specificity are class-specific. Accuracy and mean absolute delta combine classes; probability effects by class are reported separately.')
        support = pairs[MODELS[0], condition]
        row['N_phishing'] = int((support.true_label == 1).sum())
        row['N_legitimate'] = int((support.true_label == 0).sum())
        for model in MODELS:
            part = pairs[model, condition]
            row[f'{model}_mean_absolute_delta'] = float((part.C0_probability - part.probability).abs().mean()) if len(part) else np.nan
        for item in primary:
            if item['condition'] == condition:
                for metric in ('recall', 'false_positive_rate', 'specificity', 'false_negative_rate',
                               'accuracy', 'N_positive', 'N_negative'):
                    row[f"{item['model']}_{metric}"] = item[metric]
        wide.append(row)
    output = Path(output_dir)
    for name, rows in [('primary_tests', tests), ('secondary_tests', secondary), ('bootstrap_intervals', intervals),
                       ('model_condition_effects', effects), ('distance_associations', associations),
                       ('available_pair_probability_effects', available_effects),
                       ('available_pair_distance_associations', available_slopes),
                       ('multiple_comparison_adjustment', tests + secondary)]:
        _table(output, 'statistics', name, rows)
    for name, rows in [('condition_performance', wide), ('false_positive_transitions', transitions),
                       ('available_pair_false_positive_transitions', available_transitions),
                       ('primary_metrics', primary), ('available_pair_metrics', available)]:
        _table(output, 'tables', name, rows)
    has_available_pairs = any(len(available_pairs[model, condition]) for model in MODELS for condition in CONDITIONS[1:])
    state = 'COMPLETED_EXPLORATORY_PRIMARY' if eligible else ('NOT_RUN_PRIMARY_NO_COMPLETE_CASES_AVAILABLE_PAIRS_AVAILABLE' if has_available_pairs else 'NOT_RUN_PRIMARY_NO_COMPLETE_CASES_NO_AVAILABLE_PAIRS')
    status = dict(status=state, primary_frames=len(eligible), bootstrap_replicates=bootstrap_replicates,
                  seed=seed, bootstrap_unit='frame', primary_family_size=24, correction='Holm',
                  notes='Undefined quantities are blank. Primary tests use common complete frames. Available-pair metrics are separate. Exploratory associations are not causal.')
    _write(output / 'statistics/statistical_status.json', json.dumps(status, indent=2, sort_keys=True) + '\n')
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', default='data/benchmark_v3_2/frozen/robustness_matrix.csv')
    parser.add_argument('--predictions-dir', default='results/benchmark_v3_2/predictions')
    parser.add_argument('--output-dir', default='results/benchmark_v3_2')
    args = parser.parse_args()
    analyze(args.matrix, args.predictions_dir, args.output_dir)


if __name__ == '__main__':
    main()
