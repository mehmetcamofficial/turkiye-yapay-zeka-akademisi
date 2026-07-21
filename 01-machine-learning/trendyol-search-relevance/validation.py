"""Leakage-aware validation split utilities."""
from __future__ import annotations
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split

def make_split(frame: pd.DataFrame, split_type: str="term_group", seed: int=42, test_size: float=.2):
    indices=frame.index.to_numpy()
    if split_type=="random_stratified":
        train_idx,val_idx=train_test_split(indices,test_size=test_size,random_state=seed,stratify=frame["label"])
    else:
        group_column={"term_group":"term_id","item_group":"item_id"}[split_type]
        splitter=GroupShuffleSplit(n_splits=1,test_size=test_size,random_state=seed)
        train_pos,val_pos=next(splitter.split(frame,frame["label"],groups=frame[group_column]))
        train_idx,val_idx=indices[train_pos],indices[val_pos]
    train=frame.loc[train_idx].reset_index(drop=True); val=frame.loc[val_idx].reset_index(drop=True)
    report={"split_type":split_type,"train_rows":len(train),"validation_rows":len(val),
            "train_positive_rate":float(train["label"].mean()),"validation_positive_rate":float(val["label"].mean()),
            "train_unique_terms":int(train["term_id"].nunique()),"validation_unique_terms":int(val["term_id"].nunique()),
            "term_overlap":int(len(set(train["term_id"]) & set(val["term_id"]))),
            "item_overlap":int(len(set(train["item_id"]) & set(val["item_id"]))),"random_seed":seed}
    return train,val,report
