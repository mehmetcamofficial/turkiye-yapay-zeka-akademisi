# Error Analysis

Saved error files contain the 500 highest-ranked false positives and 500 lowest-ranked false negatives from the 19,285-row validation set at threshold 0.5.

Observed, example-supported patterns:

- High lexical overlap can still be negative: confident false positives include category/brand-aligned jackets, power strips, sunglasses and detergents. Lexical agreement alone does not prove product intent.
- Zero-overlap positives are difficult: spelling variants and category paraphrases appear among low-score false negatives.
- F1 is 0.372 at zero overlap, 0.653 for (0, 0.2], 0.762 for (0.2, 0.5], and 0.688 above 0.5. The highest-overlap bucket contains 108 rows and should still be interpreted cautiously.
- One- and two-token queries have recall 0.484 and 0.490; three- and four-token queries improve to 0.584 and 0.689. Buckets above six tokens are small.

Category results are reported only with row support. The largest category, sneaker (660 rows), has F1 0.718. Pants has F1 0.800 on 262 rows; sunglasses has F1 0.640 on 262 rows. Rare-category metrics are unstable and must not be generalized.

Potential causes such as synonyms, spelling variation, broad intent and attribute-driven relevance are stated only where visible in saved examples. No causal or production claim is made.
