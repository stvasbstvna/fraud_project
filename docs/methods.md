# Methods Summary

This project uses a feature-based machine learning approach for banking smishing detection. The main datasets are Smishing-4C, SmishTank, and PhiUSIIL. Smishing-4C will be used for tactically labeled smishing examples, SmishTank will be used for newer real-world smishing messages, and PhiUSIIL will be used to inform phishing-related URL features.

For the SMS text, I plan to use standard text representations such as Bag of Words and TF-IDF. I will also test tactic-aware SMS features, including message length, spelling irregularities, phone-number presence, URL presence, slang, and company or brand mentions. In addition, I plan to include URL-related features such as domain similarity, suspicious URL structure, and indicators of likely legitimacy.

The main models in the project will be Random Forest and Logistic Regression. I will first build baseline text-only models, then gradually add tactic-aware SMS features and URL-related features. This staged design will help show which kinds of features contribute most to performance.

To evaluate the models, I plan to use 5-fold cross-validation and report precision, recall, F1-score, and confusion matrices. I also want to pay special attention to false positives and false negatives, since a useful banking smishing detector should not only catch malicious messages, but also avoid misclassifying ordinary messages too often.

