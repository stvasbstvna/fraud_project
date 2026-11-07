import pandas as pd
import pytest
from tests.benchmark_v2_1.test_pipeline import frame, matrix


def test_import_only_human_approved_sources():
    from src.benchmark_v2_1.review_sources import import_reviews
    from src.benchmark_v2_1.core import source_digest,REVIEW_FIELDS
    f=frame();f['review_status']='pending'
    rv=[{'frame_id':'F1','source_sha256':source_digest(f),'reviewer':who,'decision':'approved',
        **{k:'yes' for k in REVIEW_FIELDS}} for who in ['A','B']]
    out=import_reviews(pd.DataFrame([f]),rv)
    assert out.iloc[0].review_status=='approved'
    assert import_reviews(pd.DataFrame([f]),[]).iloc[0].review_status=='pending'


def test_assembly_retains_c0_and_rejects_missing_responses():
    from src.benchmark_v2_1.assemble_matrix import assemble
    rows=matrix()
    assert len(assemble(pd.DataFrame([frame()]),rows[1:]))==7
    with pytest.raises(ValueError):assemble(pd.DataFrame([frame()]),rows[1:-1])
