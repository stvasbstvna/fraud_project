"""Actual-data tables and figures. Missing observations produce status artifacts, never dummy results."""
import json
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
from .core import DATA, RESULTS, CONDITIONS, validate_predictions, write_csv, write_json
from .statistics import mean_ci

TABLE_FIELDS={
 'A_dataset_composition':['source_id','true_label','channel','banking_related','review_status','N'],
 'B_condition_validation':['Condition','N','Jaccard similarity','Normalized edit distance','TF-IDF cosine similarity','Surface distance','Human approval rate'],
 'C_main_performance':['Condition','LR Recall','LR FNR','LR Mean delta_p','RF Recall','RF FNR','RF Mean delta_p'],
 'D_threshold_transitions':['Condition','LR Detected_to_Missed','LR Missed_to_Detected','RF Detected_to_Missed','RF Missed_to_Detected'],
 'E_legitimate_controls':['Condition','Model','N','FPR','Legitimate_to_FP','FP_to_Legitimate'],
 'F_probability_changes':['frame_id','condition','model','true_label','original_probability','variant_probability','confidence_drop','transition'],
}
FIGURES={
 '1_recall':'X: condition C0–C6; Y: phishing recall (0–1); one line per frozen detector.',
 '2_probability_change':'X: C1–C6; Y: P(C0)−P(Ci) on phishing frames; detector-specific means and paired frame bootstrap 95% intervals.',
 '3_distance_change':'X: prespecified surface distance; Y: P(C0)−P(Ci); each point a phishing variant, color identifies detector.',
 '4_transitions':'X: condition; Y: four directional decision transitions; cells show counts separately per detector.',
 '5_trajectory':'X: C0–C6; Y: phishing probability (0–1); two detector lines and fixed 0.5 threshold. Frame nearest median mean absolute paired shift, ties by stable ID.',
}


def export_table(name, rows):
    fields=TABLE_FIELDS[name]
    write_csv(RESULTS/f'tables/{name}.csv',rows,fields)
    # No optional tabulate dependency.
    lines=['| '+' | '.join(fields)+' |','| '+' | '.join(['---']*len(fields))+' |']
    for row in rows:lines.append('| '+' | '.join(str(row.get(k,'')) for k in fields)+' |')
    if not rows:lines+=['','NOT RUN: no eligible reviewed evaluated observations.']
    with (RESULTS/f'tables/{name}.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')


def paired_changes(data,model,label=None):
    subset=data if label is None else data[data.true_label.eq(label)]
    original=subset[subset.condition.eq('C0')][['frame_id',f'{model}_probability',f'{model}_prediction']]
    joined=subset.merge(original,on='frame_id',suffixes=('','_C0'),validate='many_to_one')
    joined['confidence_drop']=joined[f'{model}_probability_C0']-joined[f'{model}_probability']
    return joined


def build_tables(data):
    validate_predictions(data);tables={k:[] for k in TABLE_FIELDS if not k.startswith('A_')};detail=[]
    changes={m:paired_changes(data,m) for m in ('lr','rf')}
    for condition in CONDITIONS:
        subset=data[data.condition.eq(condition)]
        tables['B_condition_validation'].append(dict(zip(TABLE_FIELDS['B_condition_validation'],[
            condition,len(subset),subset.jaccard_similarity.mean(),subset.normalized_edit_distance.mean(),
            subset.tfidf_cosine_similarity.mean(),subset.surface_distance.mean(),1.])))
        perf={'Condition':condition};trans={'Condition':condition}
        for m,title in [('lr','LR'),('rf','RF')]:
            pair=changes[m];pair=pair[pair.condition.eq(condition)]
            phish=pair[pair.true_label.eq('phishing_scam')];legit=pair[pair.true_label.eq('legitimate')]
            pred=f'{m}_prediction';before=f'{pred}_C0'
            perf.update({f'{title} Recall':phish[pred].mean() if len(phish) else None,
                         f'{title} FNR':1-phish[pred].mean() if len(phish) else None,
                         f'{title} Mean delta_p':phish.confidence_drop.mean() if len(phish) else None})
            trans.update({f'{title} Detected_to_Missed':int(((phish[before]==1)&(phish[pred]==0)).sum()),
                          f'{title} Missed_to_Detected':int(((phish[before]==0)&(phish[pred]==1)).sum())})
            tables['E_legitimate_controls'].append({'Condition':condition,'Model':title,'N':len(legit),
                'FPR':legit[pred].mean() if len(legit) else None,
                'Legitimate_to_FP':int(((legit[before]==0)&(legit[pred]==1)).sum()),
                'FP_to_Legitimate':int(((legit[before]==1)&(legit[pred]==0)).sum())})
            y=subset.true_label.eq('phishing_scam').astype(int);yp=subset[pred].astype(int)
            tn,fp,fn,tp=confusion_matrix(y,yp,labels=[0,1]).ravel()
            detail.append({'condition':condition,'model':title,'N':len(y),'accuracy':accuracy_score(y,yp),
                'precision':precision_score(y,yp,zero_division=0),'recall':tp/(tp+fn) if tp+fn else None,
                'f1':f1_score(y,yp,zero_division=0),'FNR':fn/(tp+fn) if tp+fn else None,
                'FPR':fp/(fp+tn) if fp+tn else None,'TN':tn,'FP':fp,'FN':fn,'TP':tp,
                'mean_probability':subset[f'{m}_probability'].mean(),'median_probability':subset[f'{m}_probability'].median()})
        tables['C_main_performance'].append(perf);tables['D_threshold_transitions'].append(trans)
    for m,pair in changes.items():
        for r in pair[~pair.condition.eq('C0')].to_dict('records'):
            tables['F_probability_changes'].append({'frame_id':r['frame_id'],'condition':r['condition'],'model':m,
                'true_label':r['true_label'],'original_probability':r[f'{m}_probability_C0'],
                'variant_probability':r[f'{m}_probability'],'confidence_drop':r['confidence_drop'],
                'transition':f"{r[f'{m}_prediction_C0']}→{r[f'{m}_prediction']}"})
    tables['F_probability_changes'].sort(key=lambda r:(-abs(r['confidence_drop']),r['frame_id'],r['condition'],r['model']))
    return tables,detail


def figures(data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':11,'figure.dpi':160,'savefig.bbox':'tight'})
    out=RESULTS/'figures';out.mkdir(parents=True,exist_ok=True)
    def save(fig,name):
        for ext in ['png','svg']:
            path=out/f'{name}.{ext}'
            if path.exists():raise FileExistsError(path)
            fig.savefig(path)
        plt.close(fig)
    colors={'lr':'#245ea8','rf':'#b85017'};labels={'lr':'Logistic Regression','rf':'Random Forest'}
    fig,ax=plt.subplots(figsize=(7,4))
    for m in colors:
        ph=data[data.true_label.eq('phishing_scam')]
        ax.plot(CONDITIONS,[ph[ph.condition.eq(c)][f'{m}_prediction'].mean() for c in CONDITIONS],marker='o',label=labels[m],color=colors[m])
    ax.set(xlabel='Rewrite condition',ylabel='Phishing recall',ylim=(0,1));ax.legend();save(fig,'1_recall')
    fig,ax=plt.subplots(figsize=(7,4));pairs={m:paired_changes(data,m,'phishing_scam') for m in colors}
    for offset,(m,pair) in enumerate(pairs.items()):
        means=[];low=[];high=[]
        for c in CONDITIONS[1:]:
            values=pair[pair.condition.eq(c)].confidence_drop.to_numpy();mean=values.mean();ci=mean_ci(values)
            means.append(mean);low.append(mean-ci[0]);high.append(ci[1]-mean)
        ax.errorbar(np.arange(6)+offset*.12,means,yerr=[low,high],fmt='o',label=labels[m],color=colors[m])
    ax.axhline(0,color='gray',lw=1);ax.set(xticks=np.arange(6)+.06,xticklabels=CONDITIONS[1:],xlabel='Rewrite condition',ylabel='P(C0) − P(Ci)');ax.legend();save(fig,'2_probability_change')
    fig,ax=plt.subplots(figsize=(7,4))
    for m,pair in pairs.items():
        p=pair[~pair.condition.eq('C0')];ax.scatter(p.surface_distance,p.confidence_drop,s=12,alpha=.35,label=labels[m],color=colors[m])
    ax.axhline(0,color='gray',lw=1);ax.set(xlabel='Surface distance (frozen-space composite)',ylabel='P(C0) − P(Ci)',xlim=(0,1));ax.legend();save(fig,'3_distance_change')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,m in zip(axes,colors):
        p=paired_changes(data,m);counts=[]
        for label,before,after in [('phishing_scam',1,0),('phishing_scam',0,1),('legitimate',0,1),('legitimate',1,0)]:
            counts.append([int(((p.condition==c)&(p.true_label==label)&(p[f'{m}_prediction_C0']==before)&(p[f'{m}_prediction']==after)).sum()) for c in CONDITIONS[1:]])
        im=ax.imshow(counts,aspect='auto',vmin=0,cmap='Blues');ax.set(xticks=range(6),xticklabels=CONDITIONS[1:],yticks=range(4),yticklabels=['Detected → missed','Missed → detected','Legitimate → FP','FP → legitimate'],xlabel='Rewrite condition',ylabel='Decision transition',title=labels[m]);fig.colorbar(im,ax=ax,label='Frames')
    fig.tight_layout();save(fig,'4_transitions')
    shifts=pd.concat([p[~p.condition.eq('C0')][['frame_id','confidence_drop']] for p in pairs.values()])
    score=shifts.assign(absolute=shifts.confidence_drop.abs()).groupby('frame_id').absolute.mean()
    selected=sorted(score.index,key=lambda fid:(abs(score[fid]-score.median()),fid))[0]
    fig,ax=plt.subplots(figsize=(7,4));g=data[data.frame_id.eq(selected)].set_index('condition')
    for m in colors:ax.plot(CONDITIONS,g.loc[list(CONDITIONS),f'{m}_probability'],marker='o',label=labels[m],color=colors[m])
    ax.axhline(.5,color='gray',ls='--',label='Fixed threshold 0.5');ax.set(xlabel='Rewrite condition',ylabel='Phishing probability',ylim=(0,1),title=selected);ax.legend();save(fig,'5_trajectory')
    write_json(out/'representative_selection.json',{'frame_id':selected,'rule':'nearest median frame-mean absolute paired change across conditions and both models; tie stable ID'})


def main():
    frames=pd.read_csv(DATA/'source/frames.csv',keep_default_na=False)
    composition=frames.groupby(['source_id','true_label','channel','banking_related','review_status']).size().reset_index(name='N')
    export_table('A_dataset_composition',composition.to_dict('records'))
    path=DATA/'evaluation/predictions.csv'
    if not path.exists():
        for name in TABLE_FIELDS:
            if not name.startswith('A_'):export_table(name,[])
        write_json(RESULTS/'figures/figure_status.json',{'status':'NOT RUN','reason':'No eligible frozen evaluated variants','planned_figures':FIGURES})
        print('Composition reported; tables B–F and figures 1–5 NOT RUN');return
    data=pd.read_csv(path,keep_default_na=False);tables,detail=build_tables(data)
    for name,rows in tables.items():export_table(name,rows)
    write_csv(RESULTS/'tables/detailed_metrics.csv',detail,list(detail[0]));figures(data)


if __name__=='__main__':main()
