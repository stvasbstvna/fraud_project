"""Prospective template-family control; no detector/model inputs."""
from __future__ import annotations
import html
import re
from difflib import SequenceMatcher
import pandas as pd
from .core import digest

VERSION='pilot-template-v2'
BRANDS=('northstar bank','harbor credit','pioneer bank','summit financial','cedar bank','metrotrust',
        'lloyds','hsbc','barclays','natwest','santander','halifax','nationwide','chase','wells fargo',
        'bank of america','unionbank','citibank','citi','kotak mahendra bank','yes bank','axis bank',
        'hdfc','icici','sbi','tsb','metro bank','monzo','revolut','zelle','paypal')


def template_text(text,entity=''):
    text=html.unescape(str(text)).casefold()
    for name in sorted({*BRANDS,str(entity).casefold()}-{''},key=lambda x:(-len(x),x)):
        text=re.sub(r'(?<!\w)'+re.escape(name)+r'(?!\w)',' entityslot ',text)
    text=re.sub(r'\[[^\]]+\]|<[^>]+>',' variableslot ',text)
    # These event labels are explicit slots in the preserved legacy authoring
    # script, not independent templates; normalize them without rewriting data.
    text=re.sub(r'\b(?:deposit confirmation|card confirmation|transfer confirmation|security reminder|statement notification)\b',' eventslot ',text)
    text=re.sub(r'\b[a-z]+(?:bank|creditunion)\b',' entityslot ',text)
    text=re.sub(r'\d+(?:[.,:/-]\d+)*',' variableslot ',text)
    return ' '.join(re.findall(r'[a-z]+',text))


def pair_similarity(a,b):
    if a==b:return 1.,1.,True
    x,y=set(a.split()),set(b.split());j=len(x&y)/len(x|y) if x|y else 1.
    if j<.45:return j,0.,False
    s=SequenceMatcher(None,a,b,autojunk=False).ratio()
    return j,s,(j>=.80 and s>=.80) or (s>=.92 and j>=.45)


def assign_families(frame):
    data=frame.reset_index(drop=True).copy()
    normal=[template_text(r['defanged_text'],r.get('entity','')) for r in data.to_dict('records')]
    unique=sorted(set(normal));parents=list(range(len(unique)));lookup={s:i for i,s in enumerate(unique)}
    def root(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    for i,a in enumerate(unique):
        for j in range(i):
            if pair_similarity(a,unique[j])[2]:
                left,right=root(i),root(j);parents[max(left,right)]=min(left,right)
    groups={}
    for i,text in enumerate(unique):groups.setdefault(root(i),[]).append(text)
    ids={key:'TF-'+digest(VERSION+'\n'+'\n'.join(sorted(values)))[:20] for key,values in groups.items()}
    data['template_family_id']=[ids[root(lookup[text])] for text in normal]
    data['template_normalized_sha256']=[digest(text) for text in normal]
    return data


def nearest(text,entity,reference):
    a=template_text(text,entity);best=('',0.,False);matches=[]
    for r in reference:
        j,s,same=pair_similarity(a,r['normalized'])
        similarity=max(j,s)
        if similarity>best[1] or (similarity==best[1] and str(r['frame_id'])<best[0]):
            best=(str(r['frame_id']),similarity,same)
        if same:matches.append((str(r['frame_id']),similarity,True))
    # Highest-similarity compatible witness, with stable ID tie breaking. For
    # nonoverlapping texts return the nearest screened reference instead.
    return min(matches,key=lambda x:(-x[1],x[0])) if matches else best
