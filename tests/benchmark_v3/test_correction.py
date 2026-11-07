def test_payee_name_urn_slot_and_warning_suffix_do_not_split_family():
    from src.benchmark_v3.correction import corrected_structural_text
    a='You have registered Shijo as Payee. Log in at [SAFE-URL-1] and enter URN to confirm. Beware of frauds.'
    b='You have registered Sinco as Payee. Log in at [SAFE-URL-1] and enter URN <#> to confirm. Beware of frauds. Do NOT share or disclose URN to anyone.'
    assert corrected_structural_text(a)==corrected_structural_text(b)
