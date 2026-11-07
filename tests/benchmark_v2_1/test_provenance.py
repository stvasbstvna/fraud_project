import copy
import pandas as pd
import pytest
from tests.benchmark_v2_1.test_pipeline import frame, matrix


def test_generation_rejects_unbound_source_approval_strings():
    from src.benchmark_v2_1.generate_variants import make_requests
    with pytest.raises(ValueError,match='source review'):
        make_requests(pd.DataFrame([frame()]))


def test_source_review_binds_intent_and_independent_reviewers():
    from src.benchmark_v2_1.core import source_digest, verify_source_reviews, REVIEW_FIELDS
    f=frame()
    rv=[{'frame_id':f['frame_id'],'source_sha256':source_digest(f),'reviewer':who,'decision':'approved',
         **{k:'yes' for k in REVIEW_FIELDS}} for who in ['A','B']]
    verify_source_reviews([f],rv)
    changed=copy.deepcopy(f);changed['intent']='other intent'
    with pytest.raises(ValueError):verify_source_reviews([changed],rv)


def test_freeze_checks_canonical_source_not_variant_approval():
    from src.benchmark_v2_1.freeze_benchmark import verify_source_binding
    source=frame();source['review_status']='pending'
    with pytest.raises(ValueError,match='Canonical source'):
        verify_source_binding(matrix(),{'F1':source})


def test_manipulation_validation_is_bound_to_matrix():
    from src.benchmark_v2_1.freeze_benchmark import verify_manipulation_binding
    with pytest.raises(ValueError):
        verify_manipulation_binding({'input_sha256':'different','C1_lower_than_C5':True,'C1_lower_than_C6':True},'current')


def test_blank_or_substituted_generator_metadata_cannot_freeze():
    from src.benchmark_v2_1.generate_variants import verify_response
    request={'request_sha256':'sha','model':'fixed','provider':'fixed','variant_id':'F1-C1','prompt_sha256':'prompt','prompt_version':'v1'}
    with pytest.raises(ValueError):verify_response(matrix()[1],request,{}, {'max_attempts':2})


def test_real_freeze_module_has_json_available():
    import src.benchmark_v2_1.freeze_benchmark as module
    assert hasattr(module,'json')
