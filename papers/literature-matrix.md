# Top 10 Research Papers Most Relevant to My Project

This is a working summary of the 10 strongest research papers and technical sources that are shaping my project direction. I am using them to define my task, identify the literature gap, choose datasets, compare methods, and clarify my contribution.

## 1. Martínez-Mendoza et al. (Smishing-4C)

This paper is one of the most important foundations for my project. It introduces multi-class smishing classification, where messages are sorted into four types: Bank/Finance, Rewards, Dating, and SMS Service. The paper shows that for short SMS messages, simple feature-based methods can outperform heavier transformer models.

* **Task:** Multi-class smishing classification
* **Dataset:** Smishing-4C, 120 samples
* **Methods:** 6 tactic-aware features, Bag of Words, Random Forest, Logistic Regression, BERT, ERNIE
* **Findings:** Bag of Words combined with the 6-feature vector achieved an F1-score of 0.788
* **Limitations:** Very small dataset
* **Connection to my project:** This paper gives me the 6 tactic-aware SMS features and supports using lighter, explainable models for short banking smishing messages

## 2. Prasad and Chandra (PhiUSIIL)

This work focuses on the technical structure of phishing URLs. It does not analyze SMS text, but it is very useful for the URL side of my project because it provides a rich set of URL-related features.

* **Task:** Phishing URL detection
* **Dataset:** PhiUSIIL, 235,795 URLs
* **Methods:** 54 technical URL features such as domain similarity and legitimacy indicators
* **Findings:** Strong performance using security-profile-based URL analysis
* **Limitations:** Does not include SMS text or sender behavior
* **Connection to my project:** This is my main source for URL-side technical features

## 3. Amoafo et al. (Imbalance-Aware Framework)

This paper focuses on banking smishing and the class imbalance problem, where scam messages are much rarer than normal messages. It is especially useful because it supports Random Forest and introduces a practical balancing idea.

* **Task:** Banking smishing detection under class imbalance
* **Dataset:** Kaggle SMS dataset
* **Methods:** TF-IDF, structural features, Random Forest, Naive Bayes, NLPAug
* **Findings:** Random Forest reached an F1-score of 0.969
* **Limitations:** Based on one older public dataset
* **Connection to my project:** This validates Random Forest for banking-related SMS fraud and gives me a practical balancing strategy

## 4. Vanna et al. (Banking URL Phishing)

This study focuses only on phishing URLs that target banking users. It is useful because it shows that banking-specific URL analysis can be highly effective and gives many good handcrafted URL features.

* **Task:** Banking URL phishing detection
* **Dataset:** 30,469 banking URLs
* **Methods:** CNN, XGBoost, Random Forest, handcrafted URL features
* **Findings:** CNN reached 99% accuracy, while XGBoost reached 98%
* **Limitations:** Only analyzes URLs and ignores SMS content
* **Connection to my project:** This helps justify a banking-only focus and gives me more handcrafted URL features

## 5. Lochstampfor and Roy (Synthetic Conversational Dataset)

This paper studies conversational smishing, where scammers build trust over several rounds of interaction. It is useful because it shows that classical models can still perform well on more complex scam communication.

* **Task:** Multi-turn conversational scam detection
* **Dataset:** COVA, 3,201 synthetic conversations
* **Methods:** XGBoost, TF-IDF, transformer comparisons
* **Findings:** XGBoost worked better than transformer models on this dataset
* **Limitations:** The data is synthetic and may not fully reflect real human emotions
* **Connection to my project:** This supports using XGBoost and TF-IDF, especially when scam language becomes more complex

## 6. Salman et al. (Super Dataset Analysis)

This is a large benchmark study that compares many models on a very large SMS scam dataset. It is useful mainly as a structural and methodological reference.

* **Task:** Large-scale SMS scam detection benchmark
* **Dataset:** Super Dataset, 153,551 SMS messages
* **Methods:** 31 models including BERT, SVM, and FastText
* **Findings:** Deep learning performed strongly, but resource cost and imbalance remained major issues
* **Limitations:** The data is still imbalanced and not banking-specific
* **Connection to my project:** This gives me a benchmark-style structure for my own experiments and comparison section

## 7. Hosseinpour and Das (Multi-Signal Model)

This paper is especially important because it directly supports the idea of combining multiple signal types in one model.

* **Task:** Detecting evasive smishing
* **Dataset:** 84,000 messages from multiple sources
* **Methods:** NER tags, character-level CNN, DistilBERT, structural signals
* **Findings:** Multi-signal models outperformed single-signal approaches by 10–20%
* **Limitations:** High complexity and potential real-time deployment issues
* **Connection to my project:** This strongly supports my idea of combining SMS-side tactics and URL-side features

## 8. Agarwal et al. (IMC 2025 Study)

This work studies smishing infrastructure and campaign behavior at scale. It is not mainly a classifier paper, but it is very useful for justification and context.

* **Task:** Large-scale measurement of smishing infrastructure and strategies
* **Dataset:** 64,500 user reports from social media and SmishTank
* **Methods:** Metadata analysis, WHOIS, VirusTotal, and language model-assisted labeling
* **Findings:** Banks were the top target, and 86% of attacks used links
* **Limitations:** Focuses more on measurement than real-time classification
* **Connection to my project:** This gives strong evidence for why I am focusing on banks and URL-heavy smishing campaigns

## 9. Mishra and Soni (Smishing Detector System)

This paper presents an integrated detection system with multiple modules, not just simple text classification. It is useful because it gives a more system-level view of smishing detection.

* **Task:** Integrated smishing detection
* **Dataset:** Mendeley smishing dataset with 5,971 samples
* **Methods:** Text analysis, URL behavior, source code analysis, APK analysis, neural networks
* **Findings:** The combined system reached over 97% accuracy
* **Limitations:** The neural approach is harder to explain clearly
* **Connection to my project:** This gives me ideas for how a more complete unified pipeline could be designed

## 10. Sonowal and Kuppusamy (SmiDCA Model)

This work focuses on feature selection and tries to identify which variables really matter most.

* **Task:** Feature selection and binary scam classification
* **Dataset:** Almeida SMS spam dataset
* **Methods:** Correlation-based feature selection
* **Findings:** 96.4% accuracy using the top 20 features
* **Limitations:** Binary only and not tested for multi-class smishing
* **Connection to my project:** This can help me justify why I choose a specific subset of technical and tactical features

# Main Pattern I See Across These Papers

After going through these papers, a few things are becoming clear:

1. A lot of prior work still focuses on either SMS text or URLs, but not both together.
2. Many datasets are either old, too broad, or too small.
3. Random Forest, XGBoost, TF-IDF, and other structured baselines still perform very well on short or specialized smishing tasks.
4. Banking-specific focus is still not as developed as it could be.
5. Combining multiple signal types looks like one of the strongest directions in the newer literature.

# My Current Literature Gap

The main gap I see is that many studies either focus on SMS-side tactics or URL-side technical features, but not both together in one focused banking smishing system. Also, many studies are either too broad, not fresh enough, or not centered specifically on banking-related campaigns.

# My Current Contribution

At this stage, I see my contribution in three parts:

1. Building a banking-focused smishing setup instead of treating all SMS fraud as one category
2. Combining tactic-aware SMS features and technical URL features in one explainable pipeline
3. Using newer smishing sources and stronger structured baselines to reduce the context deficit of short SMS messages
