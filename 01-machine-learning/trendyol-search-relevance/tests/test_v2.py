import numpy as np
import pandas as pd
from v2_experiments import ranking_by_group,split_groups
from v21_evaluation import bootstrap_delta,split

def test_v2_group_split_has_no_overlap():
    frame=pd.DataFrame({"term_id":np.repeat(np.arange(20),2),"label":[0,1]*20})
    train,val,test,report=split_groups(frame)
    assert report["train_validation_overlap"]==report["train_test_overlap"]==report["validation_test_overlap"]==0
    assert set(train.term_id).isdisjoint(val.term_id) and set(train.term_id).isdisjoint(test.term_id)

def test_ranking_metrics_reward_correct_order():
    frame=pd.DataFrame({"term_id":[1,1,1],"label":[1,0,0]})
    good,_=ranking_by_group(frame,[1,.2,.1]); bad,_=ranking_by_group(frame,[.1,1,.2])
    assert good["ndcg@3"]>bad["ndcg@3"] and good["mrr"]>bad["mrr"]

def test_precision_recall_map_at_k_are_bounded():
    frame=pd.DataFrame({"term_id":[1,1,1,1],"label":[1,0,1,0]})
    metrics,_=ranking_by_group(frame,[.9,.8,.7,.1])
    for key in ["precision@5","recall@5","recall@10","map@5","map@10","mrr"]: assert 0<=metrics[key]<=1

def test_query_bootstrap_comparison_counts_groups():
    baseline=pd.DataFrame({"term_id":[1,2,3],"ndcg@10":[.5,.5,.5]}); candidate=pd.DataFrame({"term_id":[1,2,3],"ndcg@10":[.7,.5,.3]})
    result=bootstrap_delta(candidate,baseline,42)
    assert result["improved"]==1 and result["unchanged"]==1 and result["worsened"]==1
    assert result["ci_low"]<=result["delta"]<=result["ci_high"]

def test_v21_split_is_deterministic_and_complete():
    frame=pd.DataFrame({"term_id":np.repeat(np.arange(100),3),"item_id":np.arange(300),"label":[0,1,0]*100})
    first=split(frame,52); second=split(frame,52)
    assert first[3]==second[3]
    assert first[3]["train_validation_overlap"]==first[3]["train_holdout_overlap"]==first[3]["validation_holdout_overlap"]==0
    assert set(first[0].term_id).isdisjoint(first[2].term_id)
