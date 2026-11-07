"""Paired independent-frame comparisons; tiny-control uncertainty explicit."""
from itertools import combinations
import json
import numpy as np
import pandas as pd
from scipy.stats import binomtest, beta
from .core import RESULTS, read_json, digest, verify_hash, save_csv, save_json


def binomial_interval(success,total):
    if total==0:return None,None
    return (float(beta.ppf(.025,success,total-success+1)) if success else 0.,
            float(beta.ppf(.975,success+1,total-success)) if success<total else 1.)


def mcnemar(y,a,b):
    y=np.asarray(y);left=np.asarray(a)==y;right=np.asarray(b)==y
    b_count=int(np.sum(left & ~right));c_count=int(np.sum(~left & right))
    return {'A_correct_B_wrong':b_count,'A_wrong_B_correct':c_count,
            'p_value':float(binomtest(b_count,b_count+c_count,.5).pvalue) if b_count+c_count else 1.,
            'accuracy_difference':float(left.mean()-right.mean())}


def holm(values):
    p=np.asarray(values,float);order=np.argsort(p);out=np.empty(len(p));maximum=0.
    for rank,index in enumerate(order):
        maximum=max(maximum,min(1.,(len(p)-rank)*p[index]));out[index]=maximum
    return out.tolist()


def f1_samples(y,pred,index):
    yy=y[index];pp=pred[index]
    tp=((yy==1)&(pp==1)).sum(axis=1);fp=((yy==0)&(pp==1)).sum(axis=1);fn=((yy==1)&(pp==0)).sum(axis=1)
    return np.divide(2*tp,2*tp+fp+fn,out=np.zeros(len(tp),float),where=(2*tp+fp+fn)>0)


def main():
    folder=RESULTS/'experiment_A_detection';manifest=read_json(folder/'evaluation_manifest_all_models.json')
    verify_hash(folder/'predictions_all_models.csv',manifest['predictions_sha256'])
    frame=pd.read_csv(folder/'predictions_all_models.csv',keep_default_na=False)
    pivot=frame.pivot(index='id',columns='model',values='prediction').sort_index()
    labels=frame.drop_duplicates('id').set_index('id').loc[pivot.index,'true_binary'].to_numpy()
    generator=np.random.default_rng(42)
    strata=[np.flatnonzero(labels==x) for x in [0,1]]
    sampled=np.concatenate([generator.choice(ids,(10000,len(ids)),replace=True) for ids in strata],axis=1)
    comparisons=[]
    for a,b in combinations(sorted(pivot.columns),2):
        aa=pivot[a].to_numpy();bb=pivot[b].to_numpy()
        f1_delta=f1_samples(labels,aa,sampled)-f1_samples(labels,bb,sampled)
        comparisons.append({'model_A':a,'model_B':b,'paired_N':len(labels),**mcnemar(labels,aa,bb),
             'F1_difference':float(f1_samples(labels,aa,np.arange(len(labels))[None,:])[0]-f1_samples(labels,bb,np.arange(len(labels))[None,:])[0]),
             'F1_difference_bootstrap_low':float(np.quantile(f1_delta,.025)),'F1_difference_bootstrap_high':float(np.quantile(f1_delta,.975)),
             'bootstrap_unit':'one independent family representative; stratified by observed label','inference':'exploratory_tiny_control_sample'})
    for row,adjusted in zip(comparisons,holm([r['p_value'] for r in comparisons])):row['holm_adjusted_p']=adjusted
    intervals=[]
    for model in sorted(pivot.columns):
        correct=pivot[model].to_numpy()==labels
        for endpoint,mask,success in [('accuracy',np.ones(len(labels),bool),correct),('recall',labels==1,pivot[model].to_numpy()==1),('FPR',labels==0,pivot[model].to_numpy()==1)]:
            total=int(mask.sum());count=int((mask & success).sum());lo,hi=binomial_interval(count,total)
            intervals.append({'model':model,'endpoint':endpoint,'numerator':count,'denominator':total,
                 'estimate':count/total if total else None,'ci95_low':lo,'ci95_high':hi,'interval':'exact_Clopper_Pearson',
                 'scope':'selected machine-reviewed sample; no source/population generalization'})
    save_csv(RESULTS/'statistics/paired_model_comparisons.csv',comparisons)
    save_csv(RESULTS/'statistics/exact_metric_intervals.csv',intervals)
    save_json(RESULTS/'statistics/analysis_status.json',{'status':'EXPLORATORY','paired_tests':len(comparisons),'Holm_family':'three primary-model exact McNemar tests',
         'bootstrap_draws':10000,'bootstrap_seed':42,'independent_unit':'template family representative',
         'control_test_N':int((labels==0).sum()),'confirmatory_inference':False,
         'note':'Stratified bootstrap conditions on observed class composition; exact binomial control intervals show uncertainty absent from degenerate resamples.'})
    print(json.dumps(comparisons,indent=2))


if __name__=='__main__':main()
