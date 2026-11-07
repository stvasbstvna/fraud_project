import pandas as pd
import pytest


def row(fid,text,label='phishing_scam',entity='Aster Bank'):
    return dict(frame_id=fid,defanged_text=text,entity=entity,candidate_label=label,
                source_id='S',intent_category='account_review',selection_eligible=True)


def test_template_masking_ignores_entity_amount_and_destination():
    from src.benchmark_v2_1.pilot_templates import assign_families
    rows=[row('a','Aster Bank: payment 120.00 is pending. Review [SAFE-URL-1].'),
          row('b','Birch Bank: payment 450.00 is pending. Review [SAFE-URL-2].',entity='Birch Bank'),
          row('c','Aster Bank reminds you never to share confidential information.')]
    f=assign_families(pd.DataFrame(rows))
    assert f.loc[0,'template_family_id']==f.loc[1,'template_family_id']
    assert f.loc[0,'template_family_id']!=f.loc[2,'template_family_id']


def test_template_assignment_is_order_independent():
    from src.benchmark_v2_1.pilot_templates import assign_families
    rows=pd.DataFrame([row('a','Aster Bank: notice 1 [LINK].'),row('b','Aster Bank: notice 2 [OTHER].')])
    a=assign_families(rows).set_index('frame_id').template_family_id.to_dict()
    b=assign_families(rows.iloc[::-1]).set_index('frame_id').template_family_id.to_dict()
    assert a==b


def test_legacy_notification_event_slots_do_not_create_new_families():
    from src.benchmark_v2_1.pilot_templates import assign_families
    rows=pd.DataFrame([row('a','Aster Bank: Your deposit confirmation is available in [OFFICIAL-APP]. No reply is required.'),
                       row('b','Aster Bank: Your statement notification is available in [OFFICIAL-APP]. No reply is required.')])
    assert assign_families(rows).template_family_id.nunique()==1


def test_exact_numeric_and_html_mask_variants_share_family():
    from src.benchmark_v2_1.pilot_templates import template_text
    assert template_text('reference 1234 at 3:00')==template_text('reference &lt;#&gt; at &lt;TIME&gt;')


def test_selection_never_fills_quota_with_same_family_or_hold_rows():
    from src.benchmark_v2_1.pilot_selection import select_candidates
    rows=pd.DataFrame([{**row('a','one'), 'template_family_id':'F1'},
                       {**row('b','two'), 'template_family_id':'F1'},
                       {**row('c','three','legitimate'), 'template_family_id':'F2'},
                       {**row('d','four','legitimate'), 'template_family_id':'F3','selection_eligible':False}])
    selected=select_candidates(rows,per_label=24)
    assert len(selected)==2 and selected.template_family_id.is_unique


def test_spam_never_maps_to_phishing():
    from src.benchmark_v2_1.pilot_sources import candidate_label
    assert candidate_label('spam') is None
    assert candidate_label('Spam') is None
    assert candidate_label('Smishing')=='phishing_scam'
    assert candidate_label('ham')=='legitimate'


def test_gateway_extra_metadata_column_does_not_shift_message_or_id():
    from src.benchmark_v2_1.pilot_sources import parse_gateway
    raw=b'messageID,objectID,destination number,message,time,error in time\n0,obj,masked,"Bank notice for your card",sender,123,0\n'
    records=parse_gateway(raw)
    assert records[0]['text']=='Bank notice for your card'
    assert records[0]['row_id']=='0'
    with pytest.raises(ValueError):parse_gateway(b'bad,header\n1,2\n')


def test_personal_banking_chat_and_telecom_topup_are_not_bank_alert_controls():
    from src.benchmark_v2_1.pilot_sources import banking_control
    assert not banking_control('Can you do online transaction?')
    assert not banking_control('Your prepaid account has been refilled successfully.')
    assert banking_control('NEFT Transaction has been credited to the beneficiary account.')
    assert banking_control('Example Bank never asks for your confidential information. Never share it.')


def test_source_gate_needs_real_stage_a_reviews():
    from src.benchmark_v2_1.pilot_review import source_readiness
    f=pd.DataFrame([row('a','safe')])
    r=source_readiness(f,[])
    assert r['approved_source_frames']==0 and r['generation_allowed'] is False


def test_stage_a_digest_binds_template_and_label_evidence():
    from src.benchmark_v2_1.pilot_review import pilot_source_digest
    f={**row('a','safe'),'template_family_id':'F1','label_source':'original ham'}
    assert pilot_source_digest(f)!=pilot_source_digest({**f,'label_source':'unsupported'})


def test_source_approvals_do_not_silently_authorize_reduced_or_single_class_pilot():
    from src.benchmark_v2_1.pilot_review import pilot_source_digest,source_readiness,SOURCE_CHECKS
    f={**row('a','Aster Bank: Please review [SAFE-LINK].'),'template_family_id':'F1','license_status':'CC_BY_4_0'}
    rv=[{'frame_id':'a','source_sha256':pilot_source_digest(f),'reviewer':who,'decision':'approved',
         **{k:'yes' for k in SOURCE_CHECKS},'true_label':'phishing_scam','intent':'reviewed intent',
         'requested_action':'review','entity':'Aster Bank','destination':'[SAFE-LINK]','channel':'sms',
         'safe_text':f['defanged_text']} for who in ['A','B']]
    state=source_readiness(pd.DataFrame([f]),rv)
    assert state['approved_source_frames']==1
    assert state['generation_allowed'] is False


def test_nearest_family_witness_is_highest_similarity_not_first_match():
    from src.benchmark_v2_1.pilot_templates import nearest,template_text
    text='Bank notice: review the payment details now'
    refs=[{'frame_id':'near','normalized':template_text(text+' please')},
          {'frame_id':'exact','normalized':template_text(text)}]
    fid,score,same=nearest(text,'',refs)
    assert fid=='exact' and score==1 and same
