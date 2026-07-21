"""Sample-scoped data quality checks."""

import pandas as pd


def quality_summary(frame: pd.DataFrame, table_name: str, scope: str) -> tuple[dict, pd.DataFrame]:
    duplicate_count = int(frame.duplicated().sum())
    issues = {"table":table_name, "metric_scope":scope, "sample_rows":len(frame),
              "duplicate_count_sample":duplicate_count, "duplicate_percentage_sample":duplicate_count/max(len(frame),1)*100,
              "fully_empty_columns":[column for column in frame if frame[column].isna().all()]}
    duplicate = pd.DataFrame([{"table":table_name,"duplicate_count_sample":duplicate_count,
                               "duplicate_percentage_sample":issues["duplicate_percentage_sample"],"metric_scope":scope}])
    return issues, duplicate
