"""Actual-data tables/figures for the explicitly incomplete exploratory freeze."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from .core import ROOT,DATA,RESULTS,write_json
from .automated_protocol import AUTO_RESULTS,AUTO_DATA
from .automated_io import write_csv
from .automated_available_pairs import validate_available
from .statistics import mean_ci

TABLES=AUTO_RESULTS/'tables';FIGURES=AUTO_RESULTS/'figures'
CONDITIONS=[f'C{i}' for i in range(7)]


def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [clean(v) for v in value]
    if isinstance(value,(np.integer,)):return int(value)
    if isinstance(value,(np.floating,float)):return float(value) if np.isfinite(value) else None
    return value


def export(name,rows,fields=None):
    if fields is None:fields=list(rows[0])
    write_csv(TABLES/f'{name}.csv',rows,fields)
    lines=['**Exploratory available pairs; automated semantic review, not independent human annotation.**','',
        '| '+' | '.join(fields)+' |','| '+' | '.join(['---']*len(fields))+' |']
    def cell(x):
        if x is None or (isinstance(x,float) and not np.isfinite(x)):return 'NOT AVAILABLE'
        if isinstance(x,float):return f'{x:.6f}'
        return str(x).replace('|','/').replace('\n',' ')
    lines += ['| '+' | '.join(cell(row.get(k)) for k in fields)+' |' for row in rows]
    path=TABLES/f'{name}.md'
    content='\n'.join(lines)+'\n'
    if path.exists():
        if path.read_text(encoding='utf-8')!=content:raise FileExistsError(path)
    else:
        with path.open('x',encoding='utf-8') as h:h.write(content)


def inference(data):
    rows=[];per_frame=[]
    for model in ['lr','rf']:
        for (fid,label),g in data[~data.condition.eq('C0')].groupby(['frame_id','true_label']):
            x=g.surface_distance.to_numpy(dtype=float);signed=g[f'{model}_delta'].to_numpy(dtype=float)
            for endpoint,y in [('signed_change',signed),('absolute_change',np.abs(signed))]:
                slope=float(np.polyfit(x,y,1)[0]) if len(x)>=2 and np.ptp(x)>0 else None
                corr=float(np.corrcoef(x,y)[0,1]) if len(x)>=3 and np.ptp(x)>0 and np.ptp(y)>0 else None
                per_frame.append({'model':model,'frame_id':fid,'label':label,'endpoint':endpoint,'n_variants':len(x),
                    'distance_slope':slope,'pearson_correlation':corr,'scope':'exploratory_incomplete_available_variants'})
    per=pd.DataFrame(per_frame)
    for (model,label,endpoint),g in per.groupby(['model','label','endpoint']):
        valid=g.distance_slope.dropna().to_numpy(dtype=float)
        interval=mean_ci(valid) if len(valid) else (None,None)
        rows.append({'model':model,'label':label,'endpoint':endpoint,'n_frames':len(valid),'n_variants':int(g.n_variants.sum()),
            'mean_within_frame_slope':float(valid.mean()) if len(valid) else None,
            'ci95_low':interval[0],'ci95_high':interval[1],
            'mean_within_frame_correlation':g.pearson_correlation.mean(),
            'p_value':None,'inference':'descriptive_only_tiny_incomplete_cases_not_primary_family'})
    write_csv(AUTO_RESULTS/'distance_frame_effects.csv',per_frame,list(per_frame[0]))
    write_csv(AUTO_RESULTS/'distance_associations.csv',rows,list(rows[0]))
    primary=[{'hypothesis_id':hid,'n_complete_frames':0,'effect':None,'ci95_low':None,'ci95_high':None,
        'raw_p':None,'holm_adjusted_p':None,'status':'NOT RUN: no complete C0–C6 cases'}
        for hid in ['H1_DISTANCE_LOGIT','H2_DISTANCE_FN','H5_C0_C1','H6_C2_C3','H7_C0_C4','H8_C0_C5','H9_C0_C6']]
    write_csv(AUTO_RESULTS/'primary_holm_family_NOT_RUN.csv',primary,list(primary[0]))
    comparisons=[]
    for fid,g in data[~data.condition.eq('C0')].groupby('frame_id'):
        x=g.lr_delta.to_numpy(dtype=float);y=g.rf_delta.to_numpy(dtype=float)
        corr=float(np.corrcoef(x,y)[0,1]) if len(x)>=3 and np.ptp(x)>0 and np.ptp(y)>0 else None
        comparisons.append({'frame_id':fid,'n_available_variants':len(g),'lr_rf_delta_correlation':corr})
    write_csv(AUTO_RESULTS/'model_frame_comparison.csv',comparisons,list(comparisons[0]))
    return rows,comparisons


def build_tables(data):
    anchors=data[data.condition.eq('C0')]
    composition=[{k:r[k] for k in ['frame_id','source_id','original_dataset','true_label','entity','template_family_id']}
        for r in anchors.to_dict('records')]
    export('Table1_cohort_composition',composition)
    source=json.loads((AUTO_RESULTS/'source_summary.json').read_text());rewrite=json.loads((AUTO_RESULTS/'rewrite_summary.json').read_text())
    review_rows=[{'stage':'source','machine_reviewed_subjects':source['source_frames_machine_reviewed'],
        'AB_label_agreements':source['reviewer_label_agreements'],'AB_disagreements':source['reviewer_label_disagreements'],
        'adjudications':source['adjudications'],'approved':sum(source['approved_before_balancing'].values()),
        'rejected':source['rejected_source_frames'],'denominator_note':'source subjects; labels only agreement, annotation differences may also adjudicate'},
        {'stage':'rewrite','machine_reviewed_subjects':rewrite['generated_variants']-rewrite['deterministic_rejections'],
        'AB_label_agreements':None,'AB_disagreements':rewrite['rewrite_reviewer_disagreements'],
        'adjudications':rewrite['rewrite_adjudications'],'approved':rewrite['approved_generated_variants'],
        'rejected':rewrite['rejected_generated_variants'],'denominator_note':'24 generated; 8 deterministic failures never received semantic approval'}]
    export('Table2_automated_review_outcomes',review_rows)
    generated=pd.read_csv(AUTO_DATA/'reviewed_matrix.csv',keep_default_na=False)
    validation=[];metrics=[];movement=[];transitions=[];extremes=[];falsepositives=[]
    for c in CONDITIONS:
        g=data[data.condition.eq(c)]
        allg=generated[generated.condition.eq(c)]
        validation.append({'condition':c,'N_approved_available':len(g),'jaccard_similarity':g.jaccard_similarity.mean(),
            'normalized_edit_distance':g.normalized_edit_distance.mean(),'tfidf_cosine_similarity':g.tfidf_cosine_similarity.mean(),
            'surface_distance':g.surface_distance.mean(),
            'automated_approval_rate':len(g)/len(allg) if len(allg) else None,
            'scope':'C0 source approval + identity; C1–C6 machine rewrite approval; no human annotation'})
        for model in ['lr','rf']:
            n=len(g);p=g[f'{model}_probability'];pred=g[f'{model}_prediction'].astype(int)
            truth=g.true_label.eq('phishing_scam').astype(int)
            tn,fp,fn,tp=confusion_matrix(truth,pred,labels=[0,1]).ravel() if n else (0,0,0,0)
            div=lambda a,b:a/b if b else None
            metrics.append({'condition':c,'model':model,'N':n,'N_phishing':int(truth.sum()),'N_legitimate':int(n-truth.sum()),
                'accuracy':div(tp+tn,n),'precision':div(tp,tp+fp),'recall':div(tp,tp+fn),'F1':div(2*tp,2*tp+fp+fn),
                'FNR':div(fn,tp+fn),'FPR':div(fp,fp+tn),'TN':int(tn),'FP':int(fp),'FN':int(fn),'TP':int(tp),
                'mean_probability':p.mean() if n else None,'median_probability':p.median() if n else None})
            for label in ['phishing_scam','legitimate']:
                subset=g[g.true_label.eq(label)];values=subset[f'{model}_delta'].to_numpy(dtype=float)
                ci=mean_ci(values) if len(values) else (None,None)
                movement.append({'condition':c,'model':model,'label':label,'N_paired_frames':len(subset),
                    'mean_delta':float(values.mean()) if len(values) else None,'median_delta':float(np.median(values)) if len(values) else None,
                    'mean_absolute_movement':float(np.abs(values).mean()) if len(values) else None,'ci95_low':ci[0],'ci95_high':ci[1]})
                before=anchors.set_index('frame_id')[f'{model}_prediction']
                prior=subset.frame_id.map(before);after=subset[f'{model}_prediction']
                nlabel=len(subset)
                transitions.append({'condition':c,'model':model,'label':label,'N_paired_frames':nlabel,
                    'detected_to_missed':int(((prior==1)&(after==0)).sum()) if nlabel and label=='phishing_scam' else None,
                    'missed_to_detected':int(((prior==0)&(after==1)).sum()) if nlabel and label=='phishing_scam' else None,
                    'legitimate_to_FP':int(((prior==0)&(after==1)).sum()) if nlabel and label=='legitimate' else None,
                    'FP_to_legitimate':int(((prior==1)&(after==0)).sum()) if nlabel and label=='legitimate' else None})
    for model in ['lr','rf']:
        baseline=anchors.set_index('frame_id')
        for r in data.to_dict('records'):
            if r['condition']!='C0':extremes.append({'frame_id':r['frame_id'],'condition':r['condition'],'label':r['true_label'],'model':model,
                'original_probability':float(baseline.loc[r['frame_id'],f'{model}_probability']),
                'variant_probability':r[f'{model}_probability'],'delta':r[f'{model}_delta'],'absolute_movement':abs(r[f'{model}_delta']),
                'transition':f"{baseline.loc[r['frame_id'],f'{model}_prediction']}→{r[f'{model}_prediction']}",
                'selection':'ranked extreme cases, NOT representative'})
            if r['true_label']=='legitimate' and r[f'{model}_prediction']==1:falsepositives.append({'frame_id':r['frame_id'],
                'condition':r['condition'],'model':model,'probability':r[f'{model}_probability'],'safe_text':r['variant_text'],
                'label_basis':'synthetic negative control, automated semantic review; no human annotation'})
    extremes.sort(key=lambda r:(-r['absolute_movement'],r['frame_id'],r['condition'],r['model']))
    export('Table3_manipulation_check',validation);export('Table4_detector_performance',metrics)
    export('Table5_probability_movement',movement);export('Table6_decision_transitions',transitions)
    export('Table7_largest_absolute_movements',extremes);export('Table8_legitimate_false_positives',falsepositives)
    write_csv(AUTO_RESULTS/'extreme_cases.csv',extremes,list(extremes[0]))
    write_csv(AUTO_RESULTS/'prompt_trajectory_NOT_AVAILABLE.csv',[],['condition','prompt_goal','safe_resulting_text','linguistic_change','lr_probability','rf_probability','prediction','distance_from_C0'])
    return metrics,movement,transitions,extremes


def make_figures(data,metrics,movement,transitions):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    FIGURES.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'figure.dpi':170,'savefig.bbox':'tight'})
    colors={'lr':'#245ea8','rf':'#b85017'};names={'lr':'Logistic Regression','rf':'Random Forest'}
    def save(fig,name):
        for ext in ['png','svg']:
            path=FIGURES/f'{name}.{ext}'
            if path.exists():raise FileExistsError(path)
            fig.savefig(path)
        plt.close(fig)
    m=pd.DataFrame(metrics);m['recall']=pd.to_numeric(m.recall,errors='coerce')
    counts=[int(((data.condition==c)&data.true_label.eq('phishing_scam')).sum()) for c in CONDITIONS]
    fig,ax=plt.subplots(figsize=(8,4.8))
    for model,marker,ls in [('lr','o','-'),('rf','s','--')]:
        g=m[m.model.eq(model)].set_index('condition').reindex(CONDITIONS)
        ax.plot(range(7),g.recall,marker=marker,ls=ls,color=colors[model],label=names[model])
    ax.set(xticks=range(7),xticklabels=CONDITIONS,xlabel='Requested condition (gaps = no approved phishing pairs)',ylabel='Recall',ylim=(0,1.03),
        title='Exploratory available pairs — no complete C0–C6 frame\nPhishing frames by condition: '+', '.join(map(str,counts)))
    ax.legend(loc='lower right');ax.grid(alpha=.2);save(fig,'Figure1_recall_available_pairs')
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),sharey=True);mov=pd.DataFrame(movement)
    for ax,label,title in zip(axes,['phishing_scam','legitimate'],['Phishing-labelled sources','Synthetic legitimate controls']):
        for offset,model in [(-.08,'lr'),(.08,'rf')]:
            g=mov[mov.model.eq(model)&mov.label.eq(label)].set_index('condition').reindex(CONDITIONS[1:])
            means=pd.to_numeric(g.mean_delta,errors='coerce').to_numpy();lo=pd.to_numeric(g.ci95_low,errors='coerce').to_numpy();hi=pd.to_numeric(g.ci95_high,errors='coerce').to_numpy()
            ax.errorbar(np.arange(6)+offset,means,yerr=[means-lo,hi-means],fmt='o',color=colors[model],label=names[model])
        n=[int(((data.condition==c)&data.true_label.eq(label)).sum()) for c in CONDITIONS[1:]]
        ax.set(xticks=range(6),xticklabels=CONDITIONS[1:],xlabel='Rewrite condition',title=title+'\nPaired N: '+', '.join(map(str,n)),ylim=(-.18,.18))
        ax.axhline(0,color='gray',lw=1);ax.grid(alpha=.2);ax.legend(fontsize=9)
    axes[0].set_ylabel('P(C0) − P(Ci): mean (= median when N ≤ 2)')
    fig.suptitle('Observed paired score shifts; frame-bootstrap intervals; tiny N is not population precision')
    fig.tight_layout();save(fig,'Figure2_probability_change_available_pairs')
    fig,axes=plt.subplots(1,2,figsize=(11,4.7),sharex=True,sharey=True)
    variants=data[~data.condition.eq('C0')]
    for ax,model in zip(axes,['lr','rf']):
        for label,color,marker in [('phishing_scam','#b85017','o'),('legitimate','#245ea8','s')]:
            g=variants[variants.true_label.eq(label)]
            ax.scatter(g.surface_distance,g[f'{model}_delta'],c=color,marker=marker,label=label,s=35,alpha=.75)
        ax.axhline(0,color='gray',lw=1);ax.set(xlabel='Frozen-space composite surface distance',title=names[model]+'\n16 approved variants; 4 source frames',xlim=(0,1));ax.legend(fontsize=8)
    axes[0].set_ylabel('Signed paired probability change P(C0) − P(Ci)')
    fig.suptitle('Exploratory association only — variants within each frame are dependent')
    fig.tight_layout();save(fig,'Figure3_distance_movement_available_pairs')
    fig,axes=plt.subplots(1,2,figsize=(13,5.2));t=pd.DataFrame(transitions)
    specs=[('phishing_scam','detected_to_missed','Detected → missed'),('phishing_scam','missed_to_detected','Missed → detected'),
        ('legitimate','legitimate_to_FP','Legitimate → FP'),('legitimate','FP_to_legitimate','FP → legitimate')]
    for ax,model in zip(axes,['lr','rf']):
        values=[]
        for label,key,_ in specs:
            g=t[t.model.eq(model)&t.label.eq(label)].set_index('condition')
            values.append([g.loc[c,key] for c in CONDITIONS[1:]])
        array=np.array(values,dtype=float);masked=np.ma.masked_invalid(array)
        cmap=plt.get_cmap('Blues').copy();cmap.set_bad('#dddddd')
        ax.imshow(masked,aspect='auto',vmin=0,vmax=1,cmap=cmap)
        for i in range(4):
            for j in range(6):ax.text(j,i,'NA' if not np.isfinite(array[i,j]) else str(int(array[i,j])),ha='center',va='center')
        ax.set(xticks=range(6),xticklabels=CONDITIONS[1:],yticks=range(4),yticklabels=[s[2] for s in specs],xlabel='Condition',ylabel='Directional decision transition',title=names[model])
    fig.suptitle('Available paired transitions: counts; NA = no eligible pair\n4 source frames, 16 approved rewrites; denominators differ by condition/class')
    fig.tight_layout();save(fig,'Figure4_transition_counts_available_pairs')
    write_json(FIGURES/'figure_status.json',{'generated':['Figure1','Figure2','Figure3','Figure4'],
        'Figure5':'NOT AVAILABLE: no complete eligible C0–C6 frame; no representative trajectory selected',
        'Figure6':'not useful with four source frames; omitted','primary_complete_cases':0,
        'validation_type':'automated_semantic_review','scope':'exploratory_available_pairs'})


def main():
    output=DATA/'evaluation/automated_available_pairs_predictions.csv'
    from .automated_available_pairs import evaluate_available
    data=evaluate_available();validate_available(data)
    for model in ['lr','rf']:
        values=data[f'{model}_probability']
        if not np.isfinite(values).all() or not values.between(0,1).all():raise ValueError('Invalid predictions')
    evaluation=json.loads((AUTO_RESULTS/'available_pair_evaluation_manifest.json').read_text())
    if hashlib.sha256(output.read_bytes()).hexdigest()!=evaluation['predictions_sha256']:raise ValueError('Prediction evidence changed')
    metrics,movement,transitions,extremes=build_tables(data)
    distance,comparison=inference(data)
    make_figures(data,metrics,movement,transitions)
    anchors=data[data.condition.eq('C0')];variants=data[~data.condition.eq('C0')]
    wide=data.pivot(index='frame_id',columns='condition',values='surface_distance')
    manip={'primary_manipulation_validated':False,'C2_C3_paired_N':0,'reason':'No approved C2 and no complete cases'}
    for condition in ['C5','C6']:
        paired=wide[['C1',condition]].dropna();manip['C1_vs_'+condition]={'N':len(paired),'fraction_C1_lower':float((paired.C1<paired[condition]).mean()) if len(paired) else None}
    write_json(AUTO_RESULTS/'available_pair_manipulation_check.json',manip)
    summary={'status':'PRIMARY_PILOT_FAILED_COMPLETENESS_EXPLORATORY_RESULTS_AVAILABLE','review_mode':'automated',
        'source_frames':len(anchors),'source_labels':anchors.true_label.value_counts().to_dict(),'complete_case_frames':0,
        'primary_frozen_rows':0,'exploratory_frozen_rows':len(data),'approved_available_variants':len(variants),
        'all_available_rows_flagged_phishing':{m:bool(data[f'{m}_prediction'].eq(1).all()) for m in ['lr','rf']},
        'threshold_crossings':{m:int(variants[f'{m}_prediction'].ne(variants.frame_id.map(anchors.set_index('frame_id')[f'{m}_prediction'])).sum()) for m in ['lr','rf']},
        'baseline_synthetic_controls_false_positive':{m:int(anchors[anchors.true_label.eq('legitimate')][f'{m}_prediction'].sum()) for m in ['lr','rf']},
        'largest_observed_absolute_change':extremes[0],'distance_associations':clean(distance),
        'mean_within_frame_lr_rf_movement_correlation':pd.DataFrame(comparison).lr_rf_delta_correlation.mean(),
        'primary_Holm_family':'NOT RUN','figures_generated':4,'tables_generated':8,
        'representative_example':'NOT AVAILABLE: no complete eligible frame',
        'independent_human_annotation':False,'validation_type':'automated_semantic_review',
        'predictions_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
    write_json(AUTO_RESULTS/'results_summary.json',clean(summary))
    print(json.dumps(clean(summary),indent=2),flush=True)


if __name__=='__main__':main()
