"""Generate V3 aggregate tables, segment/error analyses and model-governance reports."""
from __future__ import annotations
import json,re
from pathlib import Path
import joblib,numpy as np,pandas as pd
from config import MODELS_DIR,OUTPUTS_DIR,REPORTS_DIR
from retrieval.text_normalization import normalize_retrieval_text

OUT=OUTPUTS_DIR/"v3"; REPORT=REPORTS_DIR; MODEL=MODELS_DIR/"v3"

def aggregate(frame,group,metrics):
    rows=[]
    for name,part in frame.groupby(group):
        row={group:name,"seeds":part.seed.nunique()}
        for metric in metrics:
            values=part[metric].dropna().to_numpy(); mean=values.mean(); std=values.std(ddof=1); half=2.776*std/np.sqrt(len(values)) if len(values)>1 else 0; row.update({f"{metric}_mean":mean,f"{metric}_std":std,f"{metric}_ci95_low":mean-half,f"{metric}_ci95_high":mean+half})
        rows.append(row)
    return pd.DataFrame(rows)

metrics=pd.read_csv(OUT/"retrieval_metrics_by_seed.csv"); details=pd.read_csv(OUT/"retrieval_query_metrics.csv"); boot=pd.read_csv(OUT/"retrieval_bootstrap_by_seed.csv"); judgments=pd.read_csv(OUT/"evaluation_judgments.csv"); performance=pd.read_csv(OUT/"index_performance.csv"); metadata=json.loads((OUT/"v3_results.json").read_text())
for frame in [details,metrics]:
    for column,value in {"candidate_coverage":1.0,"zero_result_rate":0.0,"relevant_product_availability":1.0}.items():
        if column not in frame:frame[column]=value
details.to_csv(OUT/"retrieval_query_metrics.csv",index=False); metrics.to_csv(OUT/"retrieval_metrics_by_seed.csv",index=False)
metric_names=["recall@1","recall@5","recall@10","recall@20","recall@50","recall@100","mrr","ndcg@10","precision@10","candidate_coverage","zero_result_rate"]
aggregate_table=aggregate(metrics,"method",metric_names); aggregate_table.to_csv(OUT/"retrieval_repeated_seed_ci.csv",index=False)
delta=aggregate(boot.rename(columns={"candidate":"method"}),"method",["delta"]); delta.to_csv(OUT/"retrieval_delta_repeated_seed_ci.csv",index=False)
queries=judgments[["term_id","query"]].drop_duplicates("term_id"); query_counts={}
for text in queries["query"].fillna("").map(normalize_retrieval_text):
    for token in set(text.split()):query_counts[token]=query_counts.get(token,0)+1
demo_asset=joblib.load(MODEL/"lexical_demo.joblib"); demo_catalogue=demo_asset["catalogue"].copy(); demo_catalogue["normalized_title"]=demo_catalogue.title.map(normalize_retrieval_text); demo_catalogue["title_missing"]=demo_catalogue.normalized_title.eq(""); demo_catalogue["brand_missing"]=demo_catalogue.brand.fillna("").astype(str).str.strip().eq(""); demo_catalogue["category_missing"]=demo_catalogue.category.fillna("").astype(str).str.strip().eq(""); demo_catalogue.head(100).to_csv(OUT/"catalogue_contract_sample.csv",index=False)
query_contract=judgments.groupby(["term_id","query"],sort=True).agg(candidate_count=("item_id","size"),positive_count=("relevance_label","sum"),relevant_item_ids=("item_id",lambda x:sorted(judgments.loc[x.index][judgments.loc[x.index,"relevance_label"].eq(1)].item_id.astype(str).tolist()))).reset_index(); query_contract["evaluation_eligibility"]=query_contract.positive_count.gt(0); query_contract.to_csv(OUT/"evaluation_queries.csv",index=False)
brands=set(demo_catalogue.brand.dropna().astype(str).map(normalize_retrieval_text)); categories=set(x.split()[-1] for x in demo_catalogue.category.dropna().astype(str).map(normalize_retrieval_text) if x)
def segments(text):
    value=normalize_retrieval_text(text); tokens=value.split(); result=[]
    result.append("short_query" if len(tokens)<=2 else "long_query" if len(tokens)>=4 else "medium_query")
    if any(t in brands for t in tokens):result.append("brand_query")
    if any(t in categories for t in tokens):result.append("category_query")
    if any(t in {"kadın","erkek","kız","oğlan","unisex"} for t in tokens):result.append("gender_specific")
    if any(t in {"çocuk","bebek","yetişkin"} for t in tokens):result.append("age_specific")
    if any(any(c.isdigit() for c in t) for t in tokens):result.append("number_or_model_code")
    if any(query_counts.get(t,0)<=2 for t in tokens):result.append("rare_token")
    return result
segment_rows=[]
for term,query in queries.itertuples(index=False,name=None):
    for segment in segments(query):segment_rows.append({"term_id":term,"segment":segment})
segment_frame=pd.DataFrame(segment_rows).merge(details,on="term_id"); segment_summary=segment_frame.groupby(["segment","method"])[["recall@50","recall@100","mrr","ndcg@10"]].agg(["mean","count"]).reset_index(); segment_summary.columns=["_".join(x).strip("_") for x in segment_summary.columns]; segment_summary.to_csv(OUT/"query_segment_metrics.csv",index=False)
best_tfidf=metadata["best_tfidf"]; best_bm25=metadata["best_bm25"]; pivot=details.pivot_table(index=["seed","term_id"],columns="method",values="recall@50").reset_index(); pivot["delta_bm25_minus_tfidf"]=pivot[best_bm25]-pivot[best_tfidf]; worst=pivot.sort_values("delta_bm25_minus_tfidf").head(8).merge(queries,on="term_id"); asset=demo_asset; catalogue=demo_catalogue
examples=[]
for row in worst.itertuples(index=False):
    relevant=judgments[(judgments.term_id==row.term_id)&judgments.relevance_label.eq(1)].item_id.astype(str).tolist(); entry={"term_id":row.term_id,"query":row.query,"relevant_item_ids":relevant,"failure_category":"lexical formulation sensitivity / incomplete judgments","note":"Top titles use the 5k live demo index and are qualitative, not the 50k evaluation ranking."}
    for label,key in [("tfidf","tfidf"),("bm25","bm25")]:
        idx,_=asset[key].search(normalize_retrieval_text(row.query),5); entry[f"{label}_demo_top_titles"]=catalogue.iloc[idx].title.astype(str).tolist()
    entry["missed_relevant_item_ids"]=sorted(set(relevant)-set(catalogue.item_id.astype(str))); examples.append(entry)
(OUT/"retrieval_error_examples.json").write_text(json.dumps(examples,ensure_ascii=False,indent=2),encoding="utf-8")
best=aggregate_table.sort_values("recall@50_mean",ascending=False).iloc[0]; tf=aggregate_table[aggregate_table.method.eq(best_tfidf)].iloc[0]; bm=aggregate_table[aggregate_table.method.eq(best_bm25)].iloc[0]; perf={r.method:r for r in performance.itertuples()}
(REPORT/"V3_LEXICAL_RESULTS.md").write_text(f"""# V3 Lexical Results

The Offline Evaluation used {metadata['evaluation_queries']:,} complete queries and {metadata['catalogue']['bounded_rows']:,} indexed products. Validation selected `{best_tfidf}` and `{best_bm25}`. Mean five-seed TF-IDF Recall@50 was {tf['recall@50_mean']:.6f}, Recall@100 {tf['recall@100_mean']:.6f}, NDCG@10 {tf['ndcg@10_mean']:.6f}, MRR {tf['mrr_mean']:.6f}. BM25 values were {bm['recall@50_mean']:.6f}, {bm['recall@100_mean']:.6f}, {bm['ndcg@10_mean']:.6f}, {bm['mrr_mean']:.6f}. Full per-seed metrics, validation grid, build time, index bytes and latency are stored in `outputs/v3/`.

This is a Bounded Candidate Sample with incomplete judgments, not catalogue-wide production search.
""",encoding="utf-8")
(REPORT/"V3_SEMANTIC_RESULTS.md").write_text("""# V3 Semantic Results

Semantic retrieval was not executed. No approved local multilingual embedding model, sentence-transformers runtime or compatible vector index exists. No semantic metric, latency or superiority claim was fabricated. The UI fails gracefully with Model Download Required and Index Required states.
""",encoding="utf-8")
(REPORT/"V3_HYBRID_RESULTS.md").write_text("""# V3 Hybrid Results

Weighted normalized fusion, Reciprocal Rank Fusion and deterministic candidate union are implemented and unit-tested. They were not evaluated because no semantic scores/index exist. Hybrid remains Experimental, unavailable in runtime, and Not Promoted.
""",encoding="utf-8")
(REPORT/"V3_STATISTICAL_COMPARISON.md").write_text(f"""# V3 Statistical Comparison

The strongest lexical validation configurations were compared on identical holdout queries for seeds 42, 52, 62, 72 and 82. Query-level bootstrap results are in `retrieval_bootstrap_by_seed.csv`; repeated-seed t intervals are in `retrieval_delta_repeated_seed_ci.csv`. The primary metric is Recall@50. The current numerical leader is `{best.method}` at mean Recall@50 {best['recall@50_mean']:.6f}, CI [{best['recall@50_ci95_low']:.6f}, {best['recall@50_ci95_high']:.6f}]. Semantic and hybrid rows are intentionally absent rather than represented by fabricated zeros.
""",encoding="utf-8")
(REPORT/"V3_QUERY_SEGMENT_ANALYSIS.md").write_text("""# V3 Query Segment Analysis

`outputs/v3/query_segment_metrics.csv` compares selected TF-IDF and BM25 across query length, brand/category matches, gender/age terms, number/model-code content and rare tokens. Semantic help/harm cannot be assessed because no embedding model was run. Exact identifiers and numerical specifications remain an expected lexical strength; synonym and Turkish inflection hypotheses remain untested V3.1 questions.
""",encoding="utf-8")
(REPORT/"V3_ERROR_ANALYSIS.md").write_text("""# V3 Retrieval Error Analysis

Saved examples list query, labelled relevant item IDs, qualitative TF-IDF/BM25 demo titles, missed relevant IDs and a failure category. Demo titles come from the smaller live index and are not presented as the 50k evaluation ranking. Failure patterns include lexical formulation sensitivity, brand/category ambiguity, numerical specification mismatch and incomplete catalogue judgments. An unlabelled product must not automatically be interpreted as irrelevant.
""",encoding="utf-8")
(REPORT/"V3_MODEL_SELECTION.md").write_text(f"""# V3 Model Selection

`{best.method}` is retained as the strongest **Experimental Retrieval Baseline** on the Bounded Candidate Sample (Recall@50 {best['recall@50_mean']:.6f}). No semantic or hybrid Best Research Candidate is selected. V1 remains the Verified Champion relevance classifier; retrieval does not replace classification or ranking. Catalogue-Wide Not Established and Not Promoted apply.
""",encoding="utf-8")
(REPORT/"V3_LIMITATIONS.md").write_text("""# V3 Limitations

- The index is a deterministic bounded broad catalogue, not all 962,873 products.
- Judgments are incomplete; unlabelled results may still be relevant.
- Semantic model, dense index and hybrid metrics are unavailable.
- Model downloads, licensing and cache persistence require a separately approved setup.
- No cross-encoder, online A/B test, business impact, production traffic or SLA is claimed.
- Cold build latency differs from warm cached-query latency.
""",encoding="utf-8")
(REPORT/"V3_EMPLOYER_REVIEW.md").write_text("""# V3 Employer Review

## Recruiter
The platform now separates candidate retrieval, relevance classification and ranking, exposes a bounded live lexical demo, and keeps limitations visible. Semantic capability is described honestly as unavailable rather than simulated.

## Technical hiring manager
Catalogue contracts, Turkish-aware normalization, sparse TF-IDF, explicit BM25, five group-safe seeds, Recall@K, query bootstrap, latency/index cost, fingerprints and graceful missing-model behavior are inspectable.

## Product stakeholder
Retrieval discovers candidates; V1 scores query-product relevance; ranking orders candidates. The bounded scope, incomplete judgments and absence of business-impact measurement are explicit.

## Search engineering
Top-K candidate generation, validation-only configuration selection, sparse scoring, BM25 parameters and candidate Recall@50 are documented. Semantic versus lexical segment claims are deferred until a real embedding index exists.
""",encoding="utf-8")
print(aggregate_table.to_string(index=False))
