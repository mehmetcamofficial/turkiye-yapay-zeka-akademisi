# Ranking Feasibility

The full one-million-row source contains 17,968 real `term_id` groups. Every group has at least two candidates and contains both positive and negative labels, so within-query ranking is feasible. Median candidates/query is 28, mean 55.65, p90 119 and maximum 6,095. Positive products/query has median 7 and p90 30.

There are 59,650 repeated `term_id`–`item_id` rows; V2 group datasets deduplicate these pairs before splitting. No synthetic ranking groups are created. Query groups remain complete in ranking-smoke and ranking-sample modes. Full mode is explicit only.
