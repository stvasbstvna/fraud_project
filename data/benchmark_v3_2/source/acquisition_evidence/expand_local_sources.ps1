$ErrorActionPreference='Stop'
$root=Get-Location
$out='data/benchmark_v3_2/source'
function HashText([string]$s) { $sha=[System.Security.Cryptography.SHA256]::Create(); return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($s)))).Replace('-','').ToLower() }
function Norm([string]$s) { return ([regex]::Replace($s.Normalize([Text.NormalizationForm]::FormKC).ToLowerInvariant(),'\s+',' ')).Trim() }
function Safe([string]$s) { $s=[regex]::Replace($s,'(?i)(?:https?://|www\.)\S+','[SAFE-URL]'); $s=[regex]::Replace($s,'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[SAFE-EMAIL]'); $s=[regex]::Replace($s,'(?<!\w)\+?\d[\d ()-]{6,}\d(?!\w)','[SAFE-NUMBER]'); return $s }
$prior=@{}; $priorText=@{}
Import-Csv data/benchmark_v3/candidates/permitted_financial_candidates.csv|ForEach-Object { $prior[$_.id]=1; if($_.origins_json){ $_.origins_json|ConvertFrom-Json|ForEach-Object { $prior[$_.id]=1 } }; $priorText[(Norm $_.safe_text)]=1 }
$reviewed=@{}; Get-ChildItem data/benchmark_v3/review/*decisions.csv|ForEach-Object { Import-Csv $_.FullName|ForEach-Object { $reviewed[$_.id]=1 } }
$pattern='\b(pay|paid|paying|repay|repayment|withdraw|withdrawal|remit|remittance|funds|cheque|cash|money|dollars?|salary|wages|posb|dbs|uob|ocbc|atm|receipt|invoice|bill|bills)\b|[$£€₹]'
$files=@(@{sid='nus';file='Singapore_smsCorpus_en_2015.03.09_all.json';url='https://github.com/kite1988/nus-sms-corpus';rights='Author public-domain copyright-free unlimited-use statement; Chen and Kan (2013)'},@{sid='mendeley';file='Mendeley_Dataset_5971.csv';url='https://data.mendeley.com/datasets/f45bkkt8pr/1';rights='CC BY 4.0; retain source attribution and change notice'},@{sid='uci';file='UCI_SMSSpamCollection';url='https://archive.ics.uci.edu/dataset/228/sms+spam+collection';rights='CC BY 4.0; Almeida and Hidalgo; retain attribution and change notice'})
$seen=@{}; $result=[Collections.Generic.List[object]]::new(); $manifest=@()
foreach($f in $files){
 $path='external/SMISH_DT/Dataset/'+$f.file; $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower(); $rows=@()
 if($f.sid -eq 'nus'){ $d=Get-Content $path -Raw -Encoding UTF8|ConvertFrom-Json; $rows=@($d.smsCorpus.message|ForEach-Object { @{rid=[string]$_.'@id';text=[string]$_.text.'$';label='unlabeled';lang=[string]$_.messageProfile.'@language'} }) }
 elseif($f.sid -eq 'mendeley'){ $i=1; $rows=@(Import-Csv $path|ForEach-Object { $r=@{rid=[string]$i;text=$_.TEXT;label=$_.LABEL;lang='en_screen_required'}; $i++; $r }) }
 else { $i=1; $rows=@(Get-Content $path -Encoding UTF8|ForEach-Object { $a=$_ -split "`t",2; $r=@{rid=[string]$i;text=$a[1];label=$a[0];lang='en_collection'}; $i++; $r }) }
 $matched=0
 foreach($r in $rows){ $id=$f.sid+'-'+$r.rid; if($prior.ContainsKey($id) -or $reviewed.ContainsKey($id) -or $r.label -match '^(spam|smishing|phishing)$' -or $r.text -notmatch $pattern){continue}; $t=Safe $r.text; $key=Norm $t; if($seen.ContainsKey($key) -or $priorText.ContainsKey($key)){continue}; $seen[$key]=1; $matched++
 $ev=([regex]::Matches($r.text,$pattern,'IgnoreCase')|ForEach-Object {$_.Value.ToLower()}|Sort-Object -Unique)-join ';'
 $result.Add([pscustomobject]@{id=$id;source_id=$f.sid;source_row_id=$r.rid;raw_label=$r.label;safe_text=$t;source_url=$f.url;origin_type='real_source_candidate';modeling_allowed='True';candidate_label='uncertain';validated_label='uncertain';message_function='pending_semantic_review';channel='sms';language='en_screen_required';source_language=$r.lang;source_file_sha256=$hash;original_text_sha256=(HashText $r.text);normalized_sha256=(HashText $key);normalized_text=$key;origins_json=('[{"id":"'+$id+'","source_id":"'+$f.sid+'"}]');rights_evidence=$f.rights;financial_evidence=$ev;selection_reason='New expanded lexical finance hit outside all prior v3 candidate IDs/text; financial-service eligibility and legitimacy NOT established';review_status='not_reviewed';duplicate_count=0})
 }
 $manifest+=@{source_id=$f.sid;path=$path;sha256=$hash;raw_rows=$rows.Count;novel_unique_lexical_candidates=$matched}
}
$ambiguous=@{}; $result|Group-Object id|Where-Object {$_.Count -gt 1}|ForEach-Object {$ambiguous[$_.Name]=1}; $result=@($result|Where-Object {-not $ambiguous.ContainsKey($_.id)}); foreach($item in $manifest){$item.novel_unique_lexical_candidates=@($result|Where-Object {$_.source_id -eq $item.source_id}).Count}; $result|Sort-Object source_id,id|Export-Csv "$out/new_source_candidates.csv" -NoTypeInformation -Encoding UTF8
@{date='2026-11-07';algorithm='Expanded lexical scan; exclude prior v3 candidate and review IDs, spam labels, exact normalized prior safe_text; deduplicate normalized safe text; no sampling; no authenticity claims';pattern=$pattern;sources=$manifest;total=$result.Count;defanging='URLs, emails, long digit sequences replaced; original hash only, no raw text exported'}|ConvertTo-Json -Depth 8|Set-Content "$out/acquisition_evidence/local_expansion_manifest.json" -Encoding UTF8
$result.Count
$result|Where-Object {$_.safe_text -match '(?i)posb|dbs|uob|ocbc|atm|withdraw|remit|funds|salary|invoice|repayment'}|Select-Object id,safe_text|Format-Table -Wrap


