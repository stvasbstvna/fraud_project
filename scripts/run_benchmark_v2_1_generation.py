"""Detector-blinded generation runner for Benchmark v2.1.

Prepared for the researcher's authorized environment. This script intentionally
refuses to run unless the explicit generation lock environment variable is set.
It never reads detector outputs.
"""
from __future__ import annotations
import argparse, json, os, re, time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

LOCK_ENV="BENCHMARK_V2_1_GENERATION_AUTHORIZED"
LIVE_URL = re.compile(r"https?://|\bwww\.", re.I)
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "frame_id": {"type": "string"},
        "condition": {"type": "string", "enum": ["C1", "C2", "C3", "C4", "C5", "C6"]},
        "text": {"type": "string"},
        "semantic_intent_preserved": {"type": "boolean"},
        "requested_action_preserved": {"type": "boolean"},
        "entity_preserved": {"type": "boolean"},
        "destination_preserved": {"type": "boolean"},
        "safety_state_preserved": {"type": "boolean"},
    },
    "required": ["frame_id", "condition", "text", "semantic_intent_preserved", "requested_action_preserved", "entity_preserved", "destination_preserved", "safety_state_preserved"],
    "additionalProperties": False,
}


def validate_output(row: dict, parsed: dict) -> tuple[bool, str]:
    reasons = []
    text = str(parsed.get("text", "")).strip()
    if parsed.get("frame_id") != row["frame_id"]: reasons.append("frame_id_changed")
    if parsed.get("condition") != row["condition"]: reasons.append("condition_changed")
    if not text: reasons.append("empty_output")
    if text == str(row["anchor_text"]).strip(): reasons.append("identical_to_anchor")
    if LIVE_URL.search(text): reasons.append("live_url_or_domain")
    for field in ("semantic_intent_preserved", "requested_action_preserved", "entity_preserved", "destination_preserved", "safety_state_preserved"):
        if parsed.get(field) is not True: reasons.append(f"self_check_failed:{field}")
    for literal, name in ((row["entity"], "entity"), (row["destination"], "destination")):
        if str(literal) not in text: reasons.append(f"missing_{name}")
    return not reasons, ";".join(reasons)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("jobs",type=Path); ap.add_argument("output",type=Path); ap.add_argument("--dry-run",action="store_true"); args=ap.parse_args()
    df=pd.read_csv(args.jobs).fillna("")
    pending=df[df.generator_status.eq("not_run")].copy()
    if args.dry_run:
        print(f"dry-run: {len(pending)} generation jobs; no API calls")
        print(pending[["variant_id","condition"]].head(10).to_string(index=False)); return
    if os.getenv(LOCK_ENV)!="YES":
        raise SystemExit(f"Generation locked. Set {LOCK_ENV}=YES only after human review and FULL_FREEZE_READY sign-off.")
    try:
        from openai import OpenAI, RateLimitError
    except ImportError as e:
        raise SystemExit("Install the OpenAI SDK in the authorized environment before generation.") from e
    client=OpenAI()
    prompt_doc=Path("docs/benchmark_v2_1_prompt_package_FINAL.md").read_text(encoding="utf-8")
    outputs=[]
    for r in pending.to_dict("records"):
        payload=(f"{prompt_doc}\n\nFRAME_ID: {r['frame_id']}\nCONDITION: {r['condition']}\n"
                 f"LABEL: {r['label']}\nSEMANTIC_INTENT: {r['semantic_intent']}\nREQUESTED_ACTION: {r['requested_action']}\n"
                 f"ENTITY: {r['entity']}\nDESTINATION: {r['destination']}\nANCHOR_TEXT: {r['anchor_text']}")
        last=None
        for attempt in range(1,3):
            try:
                resp=client.responses.create(
                    model="gpt-5.4-mini-2026-03-17", input=payload,
                    temperature=0.2, top_p=1.0, max_output_tokens=500,
                    text={"format": {"type": "json_schema", "name": "benchmark_v2_1_variant", "strict": True, "schema": OUTPUT_SCHEMA}},
                )
                parsed=json.loads(resp.output_text); text=str(parsed["text"]).strip()
                valid, reason=validate_output(r, parsed)
                last={**r,"generated_text":text,"raw_output":resp.output_text,"generator_status":"completed" if valid else "rejected_objective_validation","attempt":attempt,"response_id":resp.id,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"validation_state":"passed" if valid else "failed","rejection_reason":reason}
                break
            except RateLimitError as exc:
                print(f"Rate limit while processing {r['variant_id']}: {' '.join(str(exc).split())[:300]}")
                if outputs:
                    pd.DataFrame(outputs).to_csv(args.output,index=False)
                return
            except Exception as exc:
                last={**r,"generated_text":"","generator_status":"failed_technical","attempt":attempt,"error":str(exc)}; time.sleep(1)
        outputs.append(last)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        pd.DataFrame(outputs).to_csv(args.output,index=False)
    out=pd.DataFrame(outputs)
    print(f"wrote {len(out)} generation results")
if __name__=="__main__": main()
