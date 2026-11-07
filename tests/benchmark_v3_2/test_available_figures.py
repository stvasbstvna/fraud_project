import pandas as pd
from src.benchmark_v3_2.available_figures import summarize

def test_available_pairs_produce_nonempty_class_specific_points():
    rows=pd.DataFrame([dict(frame_id='p',model='LR',condition='C1',true_label=1,probability=.8,prediction=1,signed_delta=.1,absolute_delta=.1),dict(frame_id='l',model='LR',condition='C1',true_label=0,probability=.6,prediction=1,signed_delta=-.1,absolute_delta=.1)])
    result=summarize(rows)
    assert len(result)==2 and result.N.tolist()==[1,1]
    assert result.mean_absolute_delta.tolist()==[.1,.1]
    assert not ((result.true_label==0)&(result.condition=='C6')).any()
