"""Materialize exact prompt/config artifacts, once, before any requests are prepared."""
import json
from datetime import datetime, timezone
from .core import CONFIG, write_json

PROMPTS={
 'C1':('C1_light_lexical_v1.txt','Change only a small number of ordinary words. Preserve sentence structure and action directness as closely as possible.'),
 'C2':('C2_direct_action_v1.txt','Express the existing requested action clearly and directly. Do not add an action or strengthen the consequences.'),
 'C3':('C3_softened_action_v1.txt','Express the existing requested action less directly. The reader must still be asked to perform that same action. Merely saying that information is available does not satisfy this condition.'),
 'C4':('C4_natural_normalization_v1.txt','Improve grammar, fluency, natural phrasing and awkward formatting. Retain the existing meaning, requested action and level of urgency.'),
 'C5':('C5_strong_paraphrase_v1.txt','Use substantially different vocabulary, syntax, phrase structure and sentence structure. Preserve all controlled semantic variables.'),
 'C6':('C6_high_distance_v1.txt','Make the largest safe surface-language transformation you can using vocabulary, syntax, organization and style, while preserving every controlled semantic variable. Do not invent new context to increase distance.'),
}
SCHEMA={'type':'object','properties':{'frame_id':{'type':'string'},'condition':{'type':'string','enum':list(PROMPTS)},'text':{'type':'string'}},
        'required':['frame_id','condition','text'],'additionalProperties':False}


def main():
    (CONFIG/'prompts').mkdir(parents=True,exist_ok=True)
    registry=['# Exact prompt registry — canonical-v1','',
        'C0 is the unchanged defanged source anchor; no LLM transformation. These prompts are prepared but have NOT been executed. Archived flat prompt packages are not used by this pipeline.','',
        '| Condition | Prompt version | Purpose / allowed transformation | Forbidden |','|---|---|---|---|']
    for condition,(filename,instruction) in PROMPTS.items():
        text=(f'DEFENSIVE CONTROLLED REWRITING STUDY. Condition {condition}; prompt canonical-v1.\n'
              f'{instruction}\n'
              'Work only on the supplied defanged English SMS. Preserve true label, malicious or legitimate intent, '
              'requested action, entity exactly as written, destination, communication channel, core factual scenario and safety state. '
              'Do not introduce new facts, amounts, deadlines, threats, identities, actions or destinations. '
              'Every bracketed placeholder must remain exactly the same with the same multiplicity. '
              'Keep operational details non-operational: no URLs, bare domains, IP addresses, emails, phone numbers, credentials or payment destinations. '
              'Do not make a placeholder functional. Do not attempt to improve persuasion or evade a detector. '
              'Return ONLY a JSON object with exactly frame_id, condition and text; copy frame_id and condition from the supplied payload. '
              'No Markdown or commentary. If the requested transformation cannot preserve meaning safely, do not invent a message; the transport must record an unsuccessful attempt.\n'
              'Output schema: '+json.dumps(SCHEMA,sort_keys=True)+'\n')
        with (CONFIG/'prompts'/filename).open('x',encoding='utf-8') as f:f.write(text)
        registry.append(f'| {condition} | canonical-v1 | {instruction} | Any changed invariant, added fact or functional endpoint |')
    with (CONFIG/'PROMPT_REGISTRY.md').open('x',encoding='utf-8') as f:f.write('\n'.join(registry)+'\n')
    write_json(CONFIG/'generator_config.json',{'status':'PENDING_SOURCE_REVIEW_AND_PROVIDER_EXECUTION',
        'active':False,'provider':'OpenAI','exact_model_version':'gpt-5.4-mini-2026-03-17',
        'model_availability':'NOT VERIFIED; inherited candidate, never silently substitute',
        'api_type':'Responses API; external execution/JSONL ingestion adapter',
        'temperature':.2,'top_p':1.,'seed':None,'seed_support':'not assumed',
        'generations_per_frame':6,'generations_per_frame_condition':1,'max_attempts':2,
        'retry_policy':'technical transport failure only; retain all attempts; no detector-guided or best-of selection',
        'max_output_tokens':500,'structured_output_schema':SCHEMA,'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'prompt_version':'canonical-v1','prompt_files':{k:v[0] for k,v in PROMPTS.items()},
        'detector_feedback':'prohibited','execution_status':'NOT RUN'})
    print('Six exact prompts and inactive candidate config created')


if __name__=='__main__':main()
