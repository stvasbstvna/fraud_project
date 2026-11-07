"""Frame-unit inference, never treating seven variants as seven independent samples."""
import numpy as np
from scipy.stats import ttest_1samp


def mean_ci(values, seed=42, draws=10000):
    x=np.asarray(values,dtype=float)
    if not len(x) or not np.isfinite(x).all(): raise ValueError('Finite frame effects required')
    rng=np.random.default_rng(seed)
    means=np.array([rng.choice(x,size=len(x),replace=True).mean() for _ in range(draws)])
    return tuple(float(v) for v in np.quantile(means,[.025,.975]))


def one_sample(values):
    x=np.asarray(values,dtype=float)
    if not np.isfinite(x).all(): raise ValueError('Undefined frame effects cannot be silently dropped')
    result={'n_frames':len(x),'effect_estimate':float(x.mean()) if len(x) else None}
    if len(x)<2:return {**result,'p_value':None,'status':'insufficient_frames'}
    if np.ptp(x)==0:
        return {**result,'p_value':1. if x[0]==0 else None,
                'status':'all_zero' if x[0]==0 else 'zero_variance_nonzero'}
    return {**result,'p_value':float(ttest_1samp(x,0.).pvalue),'status':'estimated'}


def holm(values):
    p=np.asarray(values,dtype=float)
    if not np.isfinite(p).all() or not ((p>=0)&(p<=1)).all():raise ValueError('Invalid p values')
    result=np.empty(len(p));running=0.
    for rank,index in enumerate(np.argsort(p)):
        running=max(running,(len(p)-rank)*p[index]);result[index]=min(1.,running)
    return result.tolist()
