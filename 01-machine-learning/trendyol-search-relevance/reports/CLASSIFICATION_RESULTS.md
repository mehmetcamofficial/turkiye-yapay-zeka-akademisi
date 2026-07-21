# Classification Results

On 7,724 deduplicated rows / 119 complete query groups, the 70/15/15 split contained 83/18/18 groups and zero overlap. Random Forest led validation with F1 0.7852, precision 0.7361, recall 0.8413, PR AUC 0.7879 and ROC AUC 0.9381. On the untouched V2 holdout it achieved F1 0.6384, precision 0.6991, recall 0.5874, PR AUC 0.6909 and ROC AUC 0.9059. The validation-to-test drop is a warning against promotion.

V1's published 100k group-validation metrics remain unchanged (F1 0.626047, precision 0.7406, recall 0.5422, PR AUC 0.716490). These numbers come from different snapshots/splits and are context, not a paired superiority test.
