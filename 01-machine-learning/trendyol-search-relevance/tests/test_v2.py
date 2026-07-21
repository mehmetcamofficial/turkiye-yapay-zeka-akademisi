import numpy as np
import pandas as pd
from v2_experiments import ranking_by_group,split_groups

def test_v2_group_split_has_no_overlap():
    frame=pd.DataFrame({"term_id":np.repeat(np.arange(20),2),"label":[0,1]*20})
    train,val,test,report=split_groups(frame)
    assert report["train_validation_overlap"]==report["train_test_overlap"]==report["validation_test_overlap"]==0
    assert set(train.term_id).isdisjoint(val.term_id) and set(train.term_id).isdisjoint(test.term_id)

def test_ranking_metrics_reward_correct_order():
    frame=pd.DataFrame({"term_id":[1,1,1],"label":[1,0,0]})
    good,_=ranking_by_group(frame,[1,.2,.1]); bad,_=ranking_by_group(frame,[.1,1,.2])
    assert good["ndcg@3"]>bad["ndcg@3"] and good["mrr"]>bad["mrr"]
