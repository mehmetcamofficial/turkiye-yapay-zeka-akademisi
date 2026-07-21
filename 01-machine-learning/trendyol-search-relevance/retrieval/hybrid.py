"""Deterministic hybrid score and rank fusion primitives."""
import numpy as np
def minmax(values):
    x=np.asarray(values,dtype=float)
    if x.size == 0:
        return x
    lo=x.min(); hi=x.max()
    return (x-lo)/(hi-lo) if hi>lo else np.zeros_like(x)
def weighted_fusion(lexical,semantic,alpha=.5):return alpha*minmax(lexical)+(1-alpha)*minmax(semantic)
def reciprocal_rank_fusion(lexical_rank,semantic_rank,k=60):return 1/(k+np.asarray(lexical_rank))+1/(k+np.asarray(semantic_rank))
def candidate_union(*rankings):
    seen=set(); result=[]
    for ranking in rankings:
        for item in ranking:
            if item not in seen:seen.add(item);result.append(item)
    return result
