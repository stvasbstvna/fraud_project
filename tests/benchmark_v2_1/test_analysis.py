import copy
import numpy as np
import pandas as pd
import pytest
from tests.benchmark_v2_1.test_pipeline import matrix


def observations():
    rows=[]
    for i in range(3):
        for j,r in enumerate(matrix()):
            r=copy.deepcopy(r);r['frame_id']=f'F{i}';r['variant_id']=f'F{i}-{r["condition"]}'
            r['defanged_text']=r['original_text']=r['defanged_text']+f' Case {i}.'
            if j==0:r['variant_text']=r['defanged_text']
            r.update(surface_distance=j/6,jaccard_similarity=1-j/6,normalized_edit_distance=j/6,
                     tfidf_cosine_similarity=1-j/6,human_review_status='approved')
            for m in ['lr','rf']:
                p=1/(1+np.exp(-(.3+(.4+i*.1)*j/6)))
                r.update({f'{m}_probability':p,f'{m}_prediction':int(p>=.5)})
            rows.append(r)
    return pd.DataFrame(rows)


def test_primary_slopes_use_three_frames_not_21_variants():
    from src.benchmark_v2_1.analyze import analyze
    results=analyze(observations())
    assert len(results)==7 and all(r['n_frames']==3 for r in results)
    assert results[0]['effect_estimate']==pytest.approx(.5)
    assert results[1]['p_value']==1.


def test_performance_and_transitions_include_reverse_direction():
    from src.benchmark_v2_1.reports import build_tables
    f=observations();f.loc[f.condition.eq('C1'),'lr_prediction']=0
    tables,detail=build_tables(f)
    row=tables['D_threshold_transitions'][1]
    assert row['LR Detected_to_Missed']==3 and row['LR Missed_to_Detected']==0
    assert len(detail)==14 and len(tables['F_probability_changes'])==36


def test_objective_measurements_use_frozen_vectorizer_without_fit():
    from src.benchmark_v2_1.measure_distances import measure
    from sklearn.feature_extraction.text import TfidfVectorizer
    v=TfidfVectorizer().fit(['ordinary wording bank notice'])
    class Frozen:
        def transform(self,texts):return v.transform(texts)
    rows=matrix();result=measure(pd.DataFrame(rows),{'lr':Frozen(),'rf':Frozen()})
    assert result.iloc[0].surface_distance==0.
    assert result.surface_distance.between(0,1).all()
