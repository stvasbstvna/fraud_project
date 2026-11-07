from scripts.build_benchmark_v2_1_frames import build_frames, build_jobs
from analysis.benchmark_v2_1_distance_metrics import jaccard, normalized_edit_distance
from scripts.run_benchmark_v2_1_generation import validate_output

def test_frame_counts():
    f=build_frames(24,24); assert len(f)==48; assert f.frame_id.is_unique

def test_seven_conditions():
    f=build_frames(3,2); j=build_jobs(f); assert len(j)==35; assert (j.groupby('frame_id').condition.nunique()==7).all()

def test_urls_are_placeholders():
    f=build_frames(24,24); assert f.anchor_text.str.contains('https?://',regex=True).sum()==0

def test_c0_only_prepopulated():
    j=build_jobs(build_frames(2,2)); assert j.loc[j.condition.eq('C0'),'generated_text'].str.len().gt(0).all(); assert j.loc[~j.condition.eq('C0'),'generated_text'].eq('').all()

def test_distance_identity():
    assert jaccard('same text','same text')==1.0; assert normalized_edit_distance('same','same')==0.0

def test_normalized_levenshtein_distance():
    assert normalized_edit_distance("abc", "axc") == 1 / 3
    assert normalized_edit_distance("", "abc") == 1.0

def test_generation_validation_preserves_invariants_and_defanging():
    row = {"frame_id": "F1", "condition": "C3", "anchor_text": "Northstar Bank alert [DEFANGED-ALERT-LINK]", "entity": "Northstar Bank", "destination": "[DEFANGED-ALERT-LINK]"}
    parsed = {"frame_id": "F1", "condition": "C3", "text": "Northstar Bank details remain at [DEFANGED-ALERT-LINK].", "semantic_intent_preserved": True, "requested_action_preserved": True, "entity_preserved": True, "destination_preserved": True, "safety_state_preserved": True}
    assert validate_output(row, parsed) == (True, "")
    parsed["text"] = "Northstar Bank details: https://example.com"
    valid, reason = validate_output(row, parsed)
    assert not valid and "live_url_or_domain" in reason and "missing_destination" in reason
