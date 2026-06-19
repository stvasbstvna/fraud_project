# Comparative Analysis of Smishing Detection Research and Datasets

## 1. Martínez-Mendoza et al. (2024)

**Task:** Multi-class smishing detection

**Scope:** General smishing, with Bank/Finance as one class

**Signal type:** SMS-focused, with URL presence used as one tactical feature

**Approach:** Feature-based and transformer baselines compared

**Data scale:** Small (Smishing-4C has 120 labeled samples)

**Strongest confirmed result:** The combination of Bag of Words and the 6-feature vector reaches F1 0.788 and outperforms transformer-based models on this dataset

**Open gap:** The dataset is extremely small, and banking smishing is not isolated as the only target task

## 2. Mishra and Soni (2020)
**Task:** Binary smishing detection

**Scope:** General smishing

**Signal type:** SMS + URL behavior

**Approach:** Feature-based security model

**Data scale:** Moderate / older

**Strongest confirmed result:** The paper is important because it combines SMS content analysis with URL behavior analysis in one system

**Open gap:** It is not banking-specific and does not focus on newer campaign patterns


## 3. SmishTank Dataset I (Timko and Rahman, 2024)

**Task:** Smishing dataset resource

**Scope:** General smishing, but includes bank-related brands and real-world samples

**Signal type:** SMS + URL metadata

**Approach:** Dataset / resource paper

**Data scale:** Moderate and fresh (about 1090 public smishing samples)

**Strongest confirmed result:** It provides recent, community-submitted samples with sender, body, brand references, and URL-related metadata

**Open gap:** It still needs filtering and relabeling for banking-focused experiments

## 4. Commercial Anti-Smishing Tools (Timko and Rahman, 2023)

**Task:** Comparative evaluation of anti-smishing tools

**Scope:** General smishing

**Signal type:** SMS and real-world detection context

**Approach:** Tool evaluation

**Data scale:** Small evaluation set, but fresh and realistic

**Strongest confirmed result:** Carriers blocked only about 25–35% of smishing messages, and even stronger apps also blocked many benign messages

**Open gap:** This shows current defenses are weak, but it does not directly provide a banking-focused machine learning model

## 5. PhiUSIIL Dataset (Prasad and Chandra, 2024)

**Task:** Binary phishing URL detection

**Scope:** General phishing URLs

**Signal type:** URL only

**Approach:** Feature-based URL dataset with 54 technical parameters

**Data scale:** Large (235,795 URLs)

**Strongest confirmed result:** Strong as a URL feature source; includes URLSimilarityIndex, TLDLegitimateProb, URLTitleMatchScore, and other structural features

**Open gap:** It does not include SMS text, sender behavior, or banking-smishing context

## 6. Sánchez-Paniagua et al. (2022)

**Task:** Binary phishing URL detection

**Scope:** General phishing URLs

**Signal type:** URL only

**Approach:** ML and DL comparison for login-URL detection

**Data scale:** URL-scale

**Strongest confirmed result:** Useful because it studies phishing through realistic login URLs rather than generic homepage comparisons

**Open gap:** It does not solve SMS-side context or banking-specific message tactics


## 7. Mishra Dataset / Mendeley Data (2022)

**Task:** Multi-class dataset support (ham, spam, smishing)

**Scope:** General

**Signal type:** SMS only, with additional extracted attributes

**Approach:** Dataset support for machine learning and deep learning

**Data scale:** Moderate (5,971 messages)

**Strongest confirmed result:** Useful benchmark dataset with 3-way labels and raw text plus extracted attributes

**Open gap:** It includes older data and image-to-text conversion in data collection, and it is not banking-focused

## 8. Timko et al. (2023) User Study

**Task:** Binary human decision task (real vs fake)

**Scope:** General brands

**Signal type:** SMS with visual and contextual cues

**Approach:** Statistical / user-study analysis

**Data scale:** Small user-study scale (187 participants, 16 SMS screenshots)

**Strongest confirmed result:** Participants had more difficulty identifying real messages than fake ones

**Open gap:** It shows human confusion, but not a machine-learning solution

## 9. Hosseinpour and Das (2025)

**Task:** Smishing detection

**Scope:** General smishing

**Signal type:** Multi-signal SMS-oriented detection

**Approach:** Multi-signal model

**Data scale:** Large (84,000+ relabeled messages across five datasets)

**Strongest confirmed result:** Accuracy 97.89%, F1 0.963, AUC 99.73

**Open gap:** High-performing, but less focused on banking-specific explainable baselines

## 10. Pritom et al. (2026) Systematic Review

**Task:** Review

**Scope:** General, including banking context

**Signal type:** SMS + URL across the literature

**Approach:** Systematic review

**Data scale:** Review-scale

**Strongest confirmed result:** Strong for summarizing the current attack, defense, user, and dataset landscape

**Open gap:** It is not an experimental model paper, so it is mainly useful for framing the literature gap

## 11. Conversational Smishing Work (Lochstampfor and Roy line, 2026)

**Task:** Multi-turn conversational smishing detection

**Scope:** Multi-category, including scam categories beyond banking

**Signal type:** SMS dialogue / multi-turn conversations

**Approach:** Feature-based and transformer comparisons

**Data scale:** Larger than the earlier conversational baseline, but synthetic

**Strongest confirmed result:** Earlier work showed XGBoost + TF-IDF performed strongly on smaller conversational data; later work suggests larger data helps transformers more

**Open gap:** The data is synthetic and dialogue-based, so it is better treated as future work rather than a direct comparison to single-message banking smishing

# Main Takeaways for My Project

1. Most prior work is still binary or not narrowly focused on banking smishing.
2. Smishing-4C is highly relevant because it introduces tactic-aware multi-class smishing, but it is too small on its own.
3. SmishTank is valuable mainly because it adds freshness, real-world examples, brand references, and URL metadata.
4. PhiUSIIL is valuable not as a smishing dataset, but as a source of URL-risk features.
5. My strongest contribution is to combine banking-relevant SMS tactics with technical URL features in a focused, explainable baseline.
6. Random Forest and Logistic Regression remain defensible starting models because the literature still shows that feature-based methods can be competitive on small or specialized smishing datasets.
