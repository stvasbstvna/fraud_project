# Scientific rationale for the expanded Benchmark v2.1

The existing baselines use separately fitted word-level TF-IDF vectorizers with unigram and bigram features (`ngram_range=(1,2)`, `min_df=2`, `max_df=0.95`, `sublinear_tf=True`). Logistic Regression has a 50,000-feature cap and Random Forest a 20,000-feature cap. This representation can be sensitive to lexical and short-range phrase changes because semantically equivalent rewrites may map to different sparse vectors.

The Random Forest uses the same representation class but not an identical fitted feature space. Therefore the benchmark manipulates linguistic form while preserving meaning, then tests whether increased independently measured surface distance is associated with systematic confidence or binary-error changes.

## Preregistered dose-response family

Option B was approved before generation or detector evaluation. Two frame-aware common distance-trend tests and five scientifically nonredundant pooled condition contrasts form one seven-member Holm family. This happens to contain seven hypotheses but supersedes the older H1–H4-by-detector family. The patch's twelve pairwise tests were reduced because they duplicate the trend question and add avoidable multiplicity. Detector-by-distance interactions remain prespecified exploratory model-comparison estimates.

The expanded conditions C4-C6 are not detector-specific attacks. They are defined without reading model coefficients, tokens, probabilities, or predictions. This preserves the validity of a robustness experiment while increasing the strength and range of the independent variable.

The key scientific distinction is:

- **Invalid approach:** repeatedly alter a message after seeing detector scores until it is missed.
- **Valid approach used here:** preregister stronger semantic-preserving transformations, freeze them, then evaluate once on frozen detectors.

A large average effect is not required for the project to succeed. The study can support several possible conclusions:

1. TF-IDF detectors are robust across controlled paraphrase distance;
2. confidence shifts with distance but binary classifications remain stable;
3. selected conditions produce increased false negatives;
4. the two classifiers respond differently despite sharing the same representation;
5. legitimate banking controls expose an independent false-positive problem.
