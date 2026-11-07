"""Presentation-only available-pair gallery; never substitutes for primary inference."""
import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .core import ROOT,RESULTS,DOCS,CONDITIONS,immutable_bytes,immutable_json,immutable_text,file_sha,read,now
from .figures import _load

def summarize(data):
    return data.groupby(['model','condition','true_label'],sort=True).agg(N=('frame_id','nunique'),positive_predictions=('prediction','sum'),rate=('prediction','mean'),mean_signed_delta=('signed_delta','mean'),mean_absolute_delta=('absolute_delta','mean')).reset_index()

def generate():
    matrix,primary,data,conditions,n,sources=_load(ROOT)
    out=RESULTS/'figures_available_pairs';out.mkdir(exist_ok=True)
    existing=list(out.glob('*_metadata.json'));timestamp=read(existing[0])['generated_at'] if existing else now()
    plt.rcParams.update({'svg.hashsalt':'v32-available-presentation-v1','font.size':10})
    catalog=['# Graphs with observed data — exploratory available pairs\n\nThese plots show actual approved pairs, not the unavailable complete-case analysis. Condition cohorts differ. Points are individual source frames; no confidence interval is invented for one frame. The original frozen primary figures are preserved.\n']
    outputs=[]
    def save(slug,title,fig,table,note):
        fig.suptitle(title+'\nExploratory available pairs — condition cohorts differ',fontsize=13)
        fig.tight_layout(rect=(0,.06,1,.9))
        fig.text(.5,.015,note,ha='center',fontsize=9)
        immutable_bytes(out/f'{slug}_data.csv',table.to_csv(index=False,lineterminator='\n').encode())
        for ext in ['png','svg']:
            buf=io.BytesIO();fig.savefig(buf,format=ext,dpi=160,metadata={'Software':'v32-available'} if ext=='png' else {'Date':None})
            immutable_bytes(out/f'{slug}.{ext}',buf.getvalue())
        plt.close(fig)
        immutable_json(out/f'{slug}_metadata.json',dict(title=title,research_question=title,source_data=[s.replace('\\','/') for s in sources],filters='approved available pairs; no complete-case requirement',N={'source_frames':int(table.frame_id.nunique()) if 'frame_id' in table else None,'rows':len(table),'primary_complete_frames':n},models=['LR','RF','ModernBERT'],conditions=conditions,x_axis='Condition or frame as labelled',y_axis='As labelled on plot',main_observation=note,allowed_interpretation='Conditional descriptive paired observations',forbidden_interpretation='Primary completeness, population robustness or causal model ranking',generated_at=timestamp,script='src/benchmark_v3_2/available_figures.py'))
        catalog.append(f'## {title}\n\n![{title}](figures_available_pairs/{slug}.png)\n\n{note}\n\n[PNG](figures_available_pairs/{slug}.png) · [SVG](figures_available_pairs/{slug}.svg) · [Exact data](figures_available_pairs/{slug}_data.csv)\n')
        outputs.append(out/f'{slug}.png')
    colors={'LR':'#2776b4','RF':'#df791f','ModernBERT':'#27904b'}
    for slug,column,title in [('05_signed_movement','signed_delta','Signed probability movement: P(C0) - P(rewrite)'),('06_absolute_movement','absolute_delta','Absolute probability movement: |P(C0) - P(rewrite)|')]:
        pairs=data[data.condition.ne('C0')].copy();pairs['percentage_points']=100*pairs[column]
        fig,axes=plt.subplots(1,2,figsize=(12,5))
        for truth,ax in zip([1,0],axes):
            for i,c in enumerate(CONDITIONS[1:]):
                for j,model in enumerate(colors):
                    part=pairs[(pairs.true_label==truth)&pairs.condition.eq(c)&pairs.model.eq(model)]
                    x=i+(j-1)*.2
                    if part.empty:
                        if j==1:ax.text(x,.03,'NA',transform=ax.get_xaxis_transform(),ha='center',color='grey')
                        continue
                    values=part.percentage_points.to_numpy()
                    ax.scatter(x+np.linspace(-.035,.035,len(values)),values,color=colors[model],alpha=.7,s=40,label=model if i==0 else None)
                    ax.plot([x-.065,x+.065],[values.mean()]*2,color=colors[model],lw=3)
                count=pairs[(pairs.true_label==truth)&pairs.condition.eq(c)].frame_id.nunique()
                ax.text(i,1.01,f'N={count}',transform=ax.get_xaxis_transform(),ha='center')
            ax.set(title='Phishing' if truth else 'Legitimate',xticks=range(4),xticklabels=CONDITIONS[1:],ylabel='Probability movement (percentage points)')
            ax.axhline(0,color='grey',lw=.6)
        handles=[plt.Line2D([],[],marker='o',linestyle='',color=color,label=model) for model,color in colors.items()]
        fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.91),ncol=3)
        save(slug,title,fig,pairs,'Dots = individual source/rewrite pairs; short lines = means. NA = no approved pair; not zero.')
    summary=summarize(data)
    for truth,slug,title in [(1,'03_recall','Phishing recall on available messages'),(0,'04_false_positive_rate','Legitimate false-positive rate on available messages')]:
        table=summary[summary.true_label==truth].copy();fig,ax=plt.subplots(figsize=(10,5))
        for j,model in enumerate(colors):
            for i,c in enumerate(CONDITIONS):
                part=table[table.model.eq(model)&table.condition.eq(c)]
                if part.empty:
                    if j==1:ax.text(i,.04,'NA',ha='center',color='grey')
                    continue
                r=part.iloc[0];x=i+(j-1)*.22
                ax.bar(x,r.rate,.2,color=colors[model],label=model if i==0 else None)
                ax.text(x,r.rate+.015,f'{int(r.positive_predictions)}/{int(r.N)}',ha='center',fontsize=8)
        ax.set(xticks=range(5),xticklabels=CONDITIONS,ylim=(0,1.15),ylabel='Recall' if truth else 'False-positive rate');ax.legend(ncol=3,loc='lower left')
        save(slug,title,fig,table,'Labels = predicted phishing / actual class count. C0 uses all sources; rewrite cohorts differ. One legitimate source only.')
    # Source-level heatmaps make zero crossings visible without implying zero missing observations.
    pairs=data[data.condition.ne('C0')].copy();pairs['crossed']=pairs.threshold_transition.isin(['0->1','1->0']).astype(float)
    frames=sorted(pairs.frame_id.unique());fig,axes=plt.subplots(1,3,figsize=(13,6))
    for ax,model in zip(axes,colors):
        values=pairs[pairs.model.eq(model)].pivot(index='frame_id',columns='condition',values='crossed').reindex(index=frames,columns=CONDITIONS[1:])
        masked=np.ma.masked_invalid(values.to_numpy());cmap=plt.get_cmap('YlOrRd').copy();cmap.set_bad('#e5e5e5')
        ax.imshow(masked,vmin=0,vmax=1,cmap=cmap,aspect='auto')
        for i in range(len(frames)):
            for j in range(4):ax.text(j,i,'—' if pd.isna(values.iloc[i,j]) else str(int(values.iloc[i,j])),ha='center',va='center')
        ax.set(title=model,xticks=range(4),xticklabels=CONDITIONS[1:],yticks=range(len(frames)),yticklabels=frames if model=='LR' else [])
    save('08_observed_crossings','Observed threshold crossings by source',fig,pairs,'0 = observed unchanged decision; 1 = crossing; grey dash = no approved rewrite. Missing is not zero.')
    # A labelled partial diagnostic illustration, never the missing primary representative.
    moves=pairs.groupby('frame_id').absolute_delta.mean().sort_index();ident=(moves-moves.median()).abs().sort_values(kind='stable').index[0]
    sample=data[data.frame_id.eq(ident)].copy();fig,ax=plt.subplots(figsize=(10,5))
    for model in colors:
        part=sample[sample.model.eq(model)].set_index('condition').reindex(CONDITIONS)
        ax.plot(range(5),part.probability,marker='o',color=colors[model],label=model)
        for i,c in enumerate(CONDITIONS):
            if pd.isna(part.loc[c,'probability']):ax.text(i,.05,'NA',ha='center',color='grey')
    ax.axhline(.5,ls='--',color='grey',label='Threshold 0.5');ax.set(xticks=range(5),xticklabels=CONDITIONS,ylim=(0,1.03),ylabel='Phishing probability');ax.legend()
    save('09_partial_example',f'Partial diagnostic example: {ident}',fig,sample,'Nearest median available-frame movement; NOT a complete or primary representative. Lines break at missing conditions.')
    catalog.append('## Additional observed plots\n\n[Distance versus movement](figures/07_distance_vs_movement.png) · [Extreme case](figures/10_extreme_case.png) · [Manipulation distances](figures/M1_distance_distributions.png) · [Reviewed preservation](figures/M2_semantic_preservation.png)\n')
    immutable_text(RESULTS/'FIGURE_GALLERY.md','\n'.join(catalog))
    immutable_text(DOCS/'CORRECTION_AVAILABLE_PAIR_PRESENTATION.md','# Presentation correction\n\nThe original primary plots accurately showed zero complete cases, but were poor default illustrations of the existing available-pair results. A separate figures_available_pairs gallery now shows observed pairs, class-specific support, individual probability changes and explicit missing cells. No source, score, approval, statistical plan or frozen primary output was changed. These plots are descriptive and do not rescue primary completeness. The partial diagnostic example is explicitly not the unavailable primary representative.\n')
    immutable_json(out/'MANIFEST.json',{'purpose':'presentation-only available-pair supplement','prediction_hashes':{s:file_sha(ROOT/s) for s in sources[1:]},'files':{p.name:file_sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='MANIFEST.json'}})
    print('Created',len(outputs),'nonempty available-pair plots; gallery:',RESULTS/'FIGURE_GALLERY.md')

if __name__=='__main__':generate()
