import numpy as np


def test_exact_paired_test_and_holm():
    from src.benchmark_v3.statistics import mcnemar,holm
    assert mcnemar([1,1],[1,1],[1,1])['p_value']==1
    assert mcnemar([1]*5,[1]*5,[0]*5)['p_value']==.0625
    assert np.allclose(holm([.01,.03,.04]),[.03,.06,.06])


def test_two_controls_interval_does_not_claim_population_certainty():
    from src.benchmark_v3.statistics import binomial_interval
    lo,hi=binomial_interval(2,2)
    assert .15 < lo < .17 and hi==1
