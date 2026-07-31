# Ethics and Safety

This work evaluates defenses against text-based banking scams. It does not deploy scams, contact targets, or test live banking and email systems.

## Controls

- Keep raw messages in untracked local storage with access limited to the research team.
- Remove names, addresses, phone numbers, account identifiers, tracking codes, and active URLs when not required.
- Replace active links with safe tokens such as `[URL]`; never visit URLs found in scam data.
- Do not include real credentials, active malware, or executable attachments.
- Generate rewrites only from identified research samples and only in batches needed for the benchmark.
- Do not optimize prompts for delivery, victim targeting, credential theft, or evasion of a named production service.
- Log prompt versions and outputs; reject outputs that add harmful instructions or personal data.
- Report aggregate results and short redacted examples rather than operational scam-message collections.
- Follow licenses, terms, institutional review requirements, and responsible-disclosure procedures.

## Dual-use boundary

The scientific question requires measuring evasion, but the useful output is detector failure analysis and mitigation. Repository prompts describe controlled semantic preservation and annotation, not campaign execution. Any human-subject or live-system study requires separate ethics approval and written authorization.
