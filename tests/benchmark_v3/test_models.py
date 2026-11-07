import numpy as np
import pytest


def test_lexical_models_fit_only_supplied_train_vocabulary():
    from src.benchmark_v3.baselines import fit_models, probabilities
    models=fit_models(['Bank credited payment','Card statement ready','Verify bank locked','Suspended account verify'],[0,0,1,1])
    for model in models.values():
        assert 'heldouttoken' not in model.named_steps['tfidf'].vocabulary_
        p=probabilities(model,['heldouttoken bank notice','account verify'])
        assert p.shape==(2,) and np.all((p>=0)&(p<=1))


def test_one_class_training_refused():
    from src.benchmark_v3.baselines import fit_models
    with pytest.raises(ValueError): fit_models(['bank notice','card notice'],[1,1])


def test_single_class_holdout_does_not_invent_fpr_or_auc():
    from src.benchmark_v3.evaluation import metrics
    x=metrics([1,1],[.7,.3])
    assert x['recall']==.5 and x['false_positive_rate'] is None and x['ROC_AUC'] is None


def test_isolated_modern_probability_cache_binds_test_ids_and_model():
    from src.benchmark_v3.evaluation import validate_probability_cache
    cache={'ids':['a'],'probabilities':[.4],'model_sha256':'model','cohort_sha256':'cohort'}
    validate_probability_cache(cache,['a'],'model','cohort')
    with pytest.raises(ValueError): validate_probability_cache(cache,['b'],'model','cohort')
    with pytest.raises(ValueError): validate_probability_cache(cache,['a'],'changed','cohort')
    with pytest.raises(ValueError): validate_probability_cache(cache|{'probabilities':[1.1]},['a'],'model','cohort')
