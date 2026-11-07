"""Observed tables and scientific figures; never creates simulated results."""
from itertools import combinations
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .core import DATA,RESULTS,MODELS,read_json,save_csv,save_json,save_bytes
from .statistics import mcnemar,holm,binomial_interval

ORDER=['LR','RF','ModernBERT'];COLORS=['#2864a5','#de8733','#33836b'];CONDS=['C0','C1','C4','C5','C6']


def main():
    frame=pd.read_csv(DATA/'frozen/modeling_cohort.csv',keep_default_na=False)
    a=pd.read_csv(RESULTS/'experiment_A_detection/metrics_all_models.csv',keep_default_na=False).set_index('model').loc[ORDER]
    b=pd.read_csv(RESULTS/'experiment_B_generalization/metrics_all_models.csv',keep_default_na=False).set_index('model').loc[ORDER]
    cp=pd.read_csv(RESULTS/'experiment_C_robustness/predictions.csv',keep_default_na=False)
    cm=pd.read_csv(RESULTS/'experiment_C_robustness/condition_metrics.csv',keep_default_na=False)
    freeze=read_json(DATA/'robustness/freeze_manifest.json');acquisition=read_json(RESULTS/'acquisition_summary.json')
    np_test=int(a.iloc[0].phishing);nl_test=int(a.iloc[0].legitimate);n_test=int(a.iloc[0].N)
    table=RESULTS/'tables';figures=RESULTS/'figures';figures.mkdir(parents=True,exist_ok=True)
    source=frame.groupby(['source_id','label','origin_type']).agg(N=('id','size'),template_families=('template_family_id','nunique')).reset_index()
    split=frame.groupby(['split','label']).size().rename('N').reset_index()
    function=frame.groupby(['label','message_function']).size().rename('N').reset_index()
    save_csv(table/'01_final_source_composition.csv',source.to_dict('records'))
    save_csv(table/'02_split_composition.csv',split.to_dict('records'))
    save_csv(table/'03_message_functions.csv',function.to_dict('records'))
    save_csv(table/'04_original_detection.csv',a.reset_index().to_dict('records'))
    save_csv(table/'05_source_generalization.csv',b.reset_index().to_dict('records'))
    save_csv(table/'06_available_pair_robustness.csv',cm.to_dict('records'))
    primary=pd.read_csv(RESULTS/'statistics/paired_model_comparisons.csv',keep_default_na=False)
    save_csv(table/'07_primary_paired_comparisons.csv',primary.to_dict('records'))
    interval=pd.read_csv(RESULTS/'statistics/exact_metric_intervals.csv',keep_default_na=False)
    save_csv(table/'08_primary_exact_intervals.csv',interval.to_dict('records'))
    distance=pd.read_csv(RESULTS/'experiment_C_robustness/distance_association.csv',keep_default_na=False)
    for i,r in distance.iterrows():
        if r.frames_with_slope<2:
            distance.loc[i,['ci95_low','ci95_high']]=None
    distance['interval_note']=distance.frames_with_slope.map(lambda n:'NOT_ESTIMABLE_single_frame' if n<2 else 'exploratory_frame_bootstrap')
    save_csv(table/'09_distance_association.csv',distance.to_dict('records'))
    complete=cp[cp.frame_id.isin(freeze['complete_core_frames'])]
    complete_table=complete.groupby(['model','condition']).agg(N=('frame_id','size'),mean_signed_delta=('signed_delta','mean'),mean_absolute_delta=('absolute_delta','mean')).reset_index()
    complete_table['scope']=f'same{len(freeze["complete_core_frames"])}phishingcompleteframes_only_selected_not_primary_confirmatory'
    save_csv(table/'10_complete_phishing_core.csv',complete_table.to_dict('records'))
    attrition=[{'condition':c,'eligible':35,'generated_initial':35,'approved':freeze['condition_counts'].get(c,0),
               'rejected_or_missing':35-freeze['condition_counts'].get(c,0),'scope':'original35source_attempts_to_current_heldout_intersection; missing also includes excluded source IDs'} for c in CONDS[1:]]
    save_csv(table/'11_rewrite_attrition.csv',attrition)
    save_csv(table/'12_legitimate_false_positives.csv',cm[['model','condition','legitimate','false_positive_rate','already_false_positive','new_false_positives','recovered_false_positives']].to_dict('records'))
    ep=pd.read_csv(RESULTS/'experiment_C_robustness/extreme_cases.csv',keep_default_na=False)
    save_csv(table/'13_extreme_cases.csv',ep.head(12).to_dict('records'))
    trajectory=pd.read_csv(RESULTS/'experiment_C_robustness/representative_complete_trajectory.csv',keep_default_na=False)
    save_csv(table/'14_representative_phishing_trajectory.csv',trajectory.to_dict('records'))
    predB=pd.read_csv(RESULTS/'experiment_B_generalization/predictions_all_models.csv',keep_default_na=False)
    pivot=predB.pivot(index='id',columns='model',values='prediction').sort_index();y=predB.drop_duplicates('id').set_index('id').loc[pivot.index,'true_binary'].to_numpy()
    comparisons=[]
    for left,right in combinations(ORDER,2):comparisons.append({'model_A':left,'model_B':right,'paired_N':len(y),**mcnemar(y,pivot[left],pivot[right]),'scope':'secondary_exploratory_phishing_only_source_test'})
    for r,p in zip(comparisons,holm([r['p_value'] for r in comparisons])):r['holm_adjusted_p_secondary_family']=p
    save_csv(table/'15_source_paired_comparisons.csv',comparisons)
    source_intervals=[]
    for model in ORDER:
        lo,hi=binomial_interval(int(b.loc[model,'TP']),int(b.loc[model,'phishing']))
        source_intervals.append({'model':model,'TP':int(b.loc[model,'TP']),'N':int(b.loc[model,'phishing']),'recall':b.loc[model,'recall'],'ci95_low':lo,'ci95_high':hi,'scope':'conditional_source_phishing_recall_only'})
    save_csv(table/'16_source_recall_intervals.csv',source_intervals)
    quality=[]
    for r in frame.to_dict('records'):
        if any(x in r['safe_text'] for x in ['\ufffd','ï¿½','Ã','Â']):quality.append({'id':r['id'],'split':r['split'],'source_id':r['source_id'],'quality_flag':'upstream_encoding_mojibake_or_replacement','action':'preserved_and_disclosed_no_post_score_text_repair_or_exclusion'})
    save_csv(RESULTS/'diagnostics/upstream_encoding_flags.csv',quality,['id','split','source_id','quality_flag','action'])
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
    figure_records=[]
    def save(fig,name,caption):
        fig.text(.5,.01,caption,ha='center',fontsize=8,wrap=True)
        fig.tight_layout(rect=[0,.045,1,1])
        fig.savefig(figures/(name+'.png'),dpi=180,bbox_inches='tight');fig.savefig(figures/(name+'.svg'),bbox_inches='tight')
        plt.close(fig);figure_records.append({'figure':name,'caption':caption,'status':'OBSERVED_EXPLORATORY'})
    composition=frame.groupby(['source_id','label']).size().unstack(fill_value=0)
    fig,ax=plt.subplots(figsize=(8,4.6));composition.reindex(columns=['phishing','legitimate'],fill_value=0).plot.bar(stacked=True,ax=ax,color=['#bd5048','#388171'],rot=0)
    ax.set(ylabel='Independent template representatives',xlabel='Source dataset',title=f'Figure 1. Final machine-reviewed cohort ({sum(frame.label=="phishing")} phishing, {sum(frame.label=="legitimate")} legitimate)')
    save(fig,'Figure01_dataset_composition','Labels are automated; source and class remain strongly associated. No synthetic controls were added.')
    fig,ax=plt.subplots(figsize=(8,4.6));labels=['Financial raw\n(all rights)','Exact unique\n(all rights)','Rights-cleared\ncandidates','Reviewed model\nfamilies'];values=[acquisition['financial_candidates_all_rights'],acquisition['unique_financial_messages_all_rights'],acquisition['permitted_unique_financial_candidates'],len(frame)]
    ax.bar(labels,values,color=['#719bc1','#5a85ad','#487497','#33836b']);ax.set_yscale('log');ax.set(ylabel='Messages (log scale)',title='Figure 2. Raw size is not independent usable sample size')
    for i,v in enumerate(values):ax.text(i,v*1.08,f'{v:,}',ha='center')
    save(fig,'Figure02_raw_unique_families','Stages also apply rights and semantic filters; this is not a claim that all reductions are duplicates. Total raw source rows:234,547.')
    fig,axes=plt.subplots(1,3,figsize=(10,4))
    for ax,metric,title in zip(axes,['F1','recall','false_positive_rate'],['F1 (phishing class)',f'Phishing recall (N={np_test})',f'False-positive rate (N={nl_test})']):
        ax.bar(ORDER,a[metric].astype(float),color=COLORS);ax.set_ylim(0,1.08);ax.set_title(title);ax.tick_params(axis='x',rotation=25)
    axes[0].axhline(2*np_test/(2*np_test+nl_test),color='#555',ls='--',lw=1);axes[0].text(.05,.04,'Dashed: constant-phishing\nreference F1',transform=axes[0].transAxes,fontsize=8)
    fig.suptitle(f'Figure 3. Original held-out detection: {n_test} messages')
    save(fig,'Figure03_original_metrics','High F1 does not establish ability to reject legitimate controls. Labels are automated; inspect the small control denominator.')
    fig,axes=plt.subplots(1,3,figsize=(9,3.6))
    for ax,name in zip(axes,ORDER):
        z=np.array([[a.loc[name,'TN'],a.loc[name,'FP']],[a.loc[name,'FN'],a.loc[name,'TP']]],int);ax.imshow(z,cmap='Blues',vmin=0,vmax=np_test)
        for (i,j),v in np.ndenumerate(z):ax.text(j,i,str(v),ha='center',va='center',color='white' if v>16 else 'black')
        ax.set(xticks=[0,1],xticklabels=['Legitimate','Phishing'],yticks=[0,1],yticklabels=['Legitimate','Phishing'],xlabel='Predicted',ylabel='Reviewed label',title=name)
    fig.suptitle('Figure 4. Confusion matrices at threshold 0.5');save(fig,'Figure04_confusion_matrices',f'Labels are machine-reviewed, not independent human ground truth. Only{nl_test} negative test case(s); no real banking specificity estimate.')
    fig,ax=plt.subplots(figsize=(8,4.5));x=np.arange(3);ax.bar(x-.17,a.recall.astype(float),.34,label=f'Primary test:{np_test} phishing',color='#7fa4c7');ax.bar(x+.17,b.recall.astype(float),.34,label=f'Gateway source holdout:{int(b.iloc[0].phishing)} phishing',color='#3d7d70')
    ax.set(xticks=x,xticklabels=ORDER,ylim=(0,1.1),ylabel='Phishing recall',title='Figure 5. Conditional source generalization');ax.legend(loc='lower left')
    ntrain=(frame.split=='train').sum();nbtrain=(pd.read_csv(DATA/'frozen/source_holdout_cohort.csv').split=='train').sum()
    save(fig,'Figure05_source_generalization',f'Separate models trained on{nbtrain} versus{ntrain} rows. Gateway has no legitimate test cases; temporal evaluation NOT RUN.')
    fig,ax=plt.subplots(figsize=(8,4.5));x=np.arange(5)
    for i,(name,color) in enumerate(zip(ORDER,COLORS)):
        values=[float(cm[(cm.model==name)&(cm.condition==c)].iloc[0].recall) for c in CONDS]
        ax.plot(x+(i-1)*.04,values,marker=['o','s','^'][i],label=name,color=color)
    ax.set(xticks=x,xticklabels=CONDS,ylim=(0,1.06),ylabel='Phishing recall',title='Figure 6. Supplementary available-pair recall');ax.legend(loc='lower left')
    phish_n=[int(cm[(cm.model=='LR')&cm.condition.eq(c)].iloc[0].phishing) for c in CONDS]
    save(fig,'Figure06_rewrite_recall',f'Phishing N:{phish_n}. Cohorts differ across conditions; only{len(freeze["complete_core_frames"])} phishing frames have a complete core.')
    fig,ax=plt.subplots(figsize=(8,4.5));x=np.arange(4)
    for i,(name,color) in enumerate(zip(ORDER,COLORS)):
        values=[float(cm[(cm.model==name)&(cm.condition==c)].iloc[0].mean_absolute_delta)*100 for c in CONDS[1:]]
        ax.bar(x+(i-1)*.24,values,.24,label=name,color=color)
    ax.set(xticks=x,xticklabels=CONDS[1:],ylabel='Mean absolute score change (percentage points)',title='Figure 7. Supplementary probability movement');ax.legend()
    nn=[int(cm[(cm.model=='LR')&cm.condition.eq(c)].iloc[0].N) for c in CONDS[1:]]
    save(fig,'Figure07_probability_movement',f'Available pairs N:{nn}; uncalibrated model scores and unequal surviving cohorts limit comparison.')
    fig,ax=plt.subplots(figsize=(8,4.2))
    for i,(name,color) in enumerate(zip(ORDER,COLORS)):
        crossings=[int(cm[(cm.model==name)&cm.condition.eq(c)].iloc[0].threshold_crossings) for c in CONDS[1:]]
        ax.bar(x+(i-1)*.24,crossings,.24,label=name,color=color)
        for j,v in enumerate(crossings):ax.text(j+(i-1)*.24,v+.025,str(v),ha='center',color=color)
    ax.set(xticks=x,xticklabels=CONDS[1:],ylabel='Observed threshold crossings',title='Figure 8. Approved pairs at fixed threshold0.5');ax.set_ylim(bottom=0,top=max(1,ax.get_ylim()[1]+.2));ax.legend()
    save(fig,'Figure08_threshold_crossings',f'{freeze["accepted_rewrites"]} approved pairs per model; missing/rejected conditions are not scored as stable.')
    fig,axes=plt.subplots(1,3,figsize=(11,3.8),sharex=True)
    for ax,name in zip(axes,ORDER):
        for label,color in [('phishing','#2864a5'),('legitimate','#b45b48')]:
            g=cp[(cp.model==name)&cp.condition.ne('C0')&cp.label.eq(label)]
            if g.empty:continue
            ax.scatter(g.tfidf_cosine_distance,g.absolute_delta*100,c=color,label=label,alpha=.7,s=20)
        ax.set(title=name,xlabel='Frozen-TF-IDF cosine distance',ylabel='Absolute score change (pp)')
    axes[-1].legend(fontsize=8);fig.suptitle('Figure 9. Surface distance and probability movement')
    save(fig,'Figure09_distance_movement','Repeated points are clustered within source frames; descriptive associations do not establish linguistic causality.')
    fig,ax=plt.subplots(figsize=(8,4.5));x=np.arange(5)
    for i,(name,color) in enumerate(zip(ORDER,COLORS)):
        yy=[];lo=[];hi=[]
        for c in CONDS:
            r=cm[(cm.model==name)&cm.condition.eq(c)].iloc[0];n=int(r.legitimate)
            rate=float(r.false_positive_rate) if n else np.nan;yy.append(rate)
            l,h=binomial_interval(int(r.FP),n);lo.append(rate-l if n else np.nan);hi.append(h-rate if n else np.nan)
        ax.errorbar(x+(i-1)*.06,yy,yerr=[lo,hi],fmt=['o','s','^'][i],label=name,color=color,capsize=3)
    ax.set(xticks=x,xticklabels=CONDS,ylim=(0,1.05),ylabel='Observed control FPR (exact95%CI)',title='Figure 10. Existing false alarms on very few controls');ax.legend(loc='lower left')
    ncontrol=[int(cm[(cm.model=='LR')&cm.condition.eq(c)].iloc[0].legitimate) for c in CONDS]
    save(fig,'Figure10_legitimate_false_positives',f'Control N:{ncontrol}; gaps mean unavailable, never zeroFPR. No control generalization or unsupported new/recovered-FP conclusion.')
    for path in sorted(table.glob('*.csv')):
        df=pd.read_csv(path,keep_default_na=False)
        header='| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'
        body=''.join('| '+' | '.join(str(v).replace('|','/') for v in row)+' |\n' for row in df.head(30).itertuples(index=False,name=None))
        save_bytes(path.with_suffix('.md'),('# '+path.stem.replace('_',' ')+'\n\nExploratory machine-reviewed research; see exact denominators and limitations in FINAL_REPORT.md. CSV is authoritative; preview limited to30rows.\n\n'+header+body).encode())
    save_json(figures/'figure_status.json',{'figures':figure_records,'scientific_figure_count':len(figure_records),'tables':len(list(table.glob('*.csv'))),'observed_only':True,'validation':'automated_semantic_review_not_independent_human'})
    print(f'{len(figure_records)} figures; {len(list(table.glob("*.csv")))} tables; {len(quality)} upstream encoding flags')


if __name__=='__main__':main()
