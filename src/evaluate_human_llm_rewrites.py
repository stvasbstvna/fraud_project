"""Evaluate original human, existing LLM, and rewritten-human scenarios."""

from pathlib import Path
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

ROOT = Path("data/human_llm_rewrite_experiment")
OUT = Path("results/human_llm_rewrite_experiment")
MODEL = Path("models/tfidf_logistic_regression.joblib")

def score(model, texts):
    probs = model.predict_proba(texts.astype(str))[:, 1]
    preds = (probs >= 0.5).astype(int)
    return preds, probs

def classification_metrics(name, positives, negatives, text_col, model):
    pos = positives[["sample_id", text_col]].rename(columns={text_col:"evaluation_text"}).copy(); pos["true_binary_label"] = 1
    neg = negatives[["sample_id", "text"]].rename(columns={"text":"evaluation_text"}).copy(); neg["true_binary_label"] = 0
    data = pd.concat([pos, neg], ignore_index=True)
    pred, prob = score(model, data["evaluation_text"])
    data["prediction"] = pred; data["phishing_probability"] = prob; data["scenario"] = name
    tn, fp, fn, tp = confusion_matrix(data.true_binary_label, pred, labels=[0,1]).ravel()
    metrics = {"scenario":name,"rows":len(data),"phishing_rows":len(pos),"legitimate_rows":len(neg),
        "accuracy":accuracy_score(data.true_binary_label,pred),"precision":precision_score(data.true_binary_label,pred,zero_division=0),
        "recall":recall_score(data.true_binary_label,pred,zero_division=0),"f1":f1_score(data.true_binary_label,pred,zero_division=0),
        "fnr":fn/(fn+tp) if fn+tp else 0,"tn":tn,"fp":fp,"fn":fn,"tp":tp,"avg_phishing_probability_on_positives":float(prob[:len(pos)].mean())}
    return data, metrics

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    model = joblib.load(MODEL)
    human = pd.read_csv(ROOT/"05_matched_human_33.csv")
    llm = pd.read_csv(ROOT/"06_matched_llm_33.csv")
    rewrites = pd.read_csv(ROOT/"03_human_to_llm_rewrite_input.csv")
    controls = pd.read_csv(ROOT/"04_fixed_legitimate_banking_controls.csv")
    completed = rewrites[(rewrites.generation_status == "completed") & rewrites.rewrite_text.notna() & rewrites.same_intent_verified.eq("yes") & rewrites.no_new_operational_detail.eq("yes")].head(33)
    scenarios=[("human_original_33",human,"original_text"),("existing_llm_33",llm,"original_text")]
    if len(completed): scenarios.append(("human_llm_rewritten",completed,"rewrite_text"))
    all_predictions=[]; all_metrics=[]
    for name, positives, col in scenarios:
        pred, metrics=classification_metrics(name,positives,controls,col,model); all_predictions.append(pred); all_metrics.append(metrics)
    pd.DataFrame(all_metrics).to_csv(OUT/"classification_metrics_by_scenario.csv",index=False)
    pd.concat(all_predictions,ignore_index=True).to_csv(OUT/"predictions_by_scenario.csv",index=False)
    if len(completed):
        original=human.set_index("sample_id").loc[completed.sample_id]
        _, before=score(model,original.original_text); after_pred,after=score(model,completed.rewrite_text)
        paired=pd.DataFrame({"sample_id":completed.sample_id.values,"probability_before":before,"probability_after":after,
            "probability_drop":before-after,"became_false_negative":after_pred==0})
        paired.to_csv(OUT/"paired_rewrite_behavior.csv",index=False)
        pd.DataFrame([{"pairs":len(paired),"average_probability_before":before.mean(),"average_probability_after":after.mean(),
            "average_probability_drop":paired.probability_drop.mean(),"attack_success_rate":paired.became_false_negative.mean()}]).to_csv(OUT/"paired_rewrite_summary.csv",index=False)
    print(pd.DataFrame(all_metrics).to_string(index=False))

if __name__ == "__main__":
    main()
