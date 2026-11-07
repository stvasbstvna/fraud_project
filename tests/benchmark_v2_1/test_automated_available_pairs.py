import copy
import pandas as pd
import pytest
from tests.benchmark_v2_1.test_pipeline import matrix


def available():
    rows=[]
    for i,label in enumerate(['phishing_scam','legitimate']):
        for row in matrix()[:2]:
            row=copy.deepcopy(row);row.update(frame_id=f'F{i}',variant_id=f'F{i}-{row["condition"]}',
                true_label=label,source_id=f'S{i}',template_family_id=f'T{i}',review_mode='automated',
                automated_source_approved=True,automated_rewrite_approved=True,
                generation_request_hash='fixture',rewrite_A_hash='fixtureA',rewrite_B_hash='fixtureB')
            rows.append(row)
    return pd.DataFrame(rows)


def test_available_pair_validation_does_not_masquerade_as_complete_freeze():
    from src.benchmark_v2_1.automated_available_pairs import validate_available
    from src.benchmark_v2_1.automated_freeze import validate_automated_matrix
    frame=available();validate_available(frame)
    with pytest.raises(ValueError):validate_automated_matrix(frame)


def test_unapproved_variant_is_never_scored_as_available_pair():
    from src.benchmark_v2_1.automated_available_pairs import validate_available
    frame=available();frame.loc[1,'automated_rewrite_approved']=False
    with pytest.raises(ValueError):validate_available(frame)


def test_available_pairs_must_have_bound_baseline():
    from src.benchmark_v2_1.automated_available_pairs import validate_available
    frame=available();frame=frame[~frame.condition.eq('C0')]
    with pytest.raises(ValueError):validate_available(frame)
