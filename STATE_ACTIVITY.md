# Fixed state activity

`state_activity_methods` describes artifact hashes, scope, source gaps, units and reference vintages. Call it before interpretation. `state_activity_page` returns separate annual state CID or procedure source-record intervals. It does not query the joint table or infer patients.

## Inputs

- `kind`: `cid` or `procedure`, never a joint filter.
- `uf`: one residence state; DF and unknown residence excluded, not zero.
- `year`: one processing-file year from 2022 through 2026. 2026 is January-July only.
- `family`: `RD`, `PA` or `AM`. Do not union families into unique people.
- `code`: optional exact source string. No prefix expansion or recoding.
- `limit`: 1-100, default 100.
- `cursor`: next-page cursor from the same query and frozen artifact.

The tools require `SUS_STATE_DATA`, a directory containing `phase2-metadata.json` and its hash-frozen CID/procedure parquet files. `SUS_FOUNDATION_DATA` is also required for the shared dataset work slot. No artifacts are bundled here. Importing the adapter starts no listener. Without the opt-in the existing demo remains usable.

## Interpretation

Rows have integer `records_lower` and `records_upper` bounds, in fixed 10-wide intervals. Cells under 20 source records and additional complementary margins are absent. Missing is unknown: absence cannot distinguish suppression, missing source periods, invalid geography or lack of a code. No exact total, private patch list or residual is returned. Pagination only retrieves rows already in the frozen artifact, not new aggregates. Cursors are query/artifact-bound, not access-control credentials.

RD counts inpatient administrative source records, not deduplicated admissions. PA counts ambulatory billing source records, not approved quantities. AM counts medication APAC source records, not doses, prescriptions, vials or actual dispensing. None counts people or disease prevalence. PA placeholders such as 0000/1111 are not diagnoses. Preserve exact raw strings and dated labels; a same-year dictionary match does not prove record-date validity.

The fixed source gaps and publisher-reconciliation limits remain in methods and results. In particular AM independent publisher record totals remain unverified, PA quantity reconciliation does not establish record-count agreement, and RD has documented differences. Processing-file years are not necessarily care dates. Full-year results must not be compared with partial 2026 as matched periods; coding changes and missing files can change recorded ascertainment.

## Frozen source-file coverage

The live methods and each page explicitly retain the following warning. These are gaps in the frozen collection, not a current availability claim or zero activity:

| AM processing year | Billing-UF/month files absent from the collection |
| --- | --- |
| 2022 | AC June/September; AM January; RS June/July/August |
| 2023 | AP March; MA April; PB July |
| 2024 | AM October; AP September/October; RS April/May |
| 2025 | AP June; TO May |
| January-July 2026 | AL May; MA/PB/RO July |

RD January-July 2026 lacks July AC and RR files. RD2022-2025 has all expected billing-UF/month slots. PA has all expected slots in each included processing-file window, sometimes through split files. Complete slots do not establish complete clinical ascertainment, valid residence or independent publisher reconciliation.

A missing billing-UF file can affect residents of other states, not only residents of that billing state. AM has gaps in every included year, so cross-year AM activity is not automatically like-for-like. Missing files must not be treated as zero. Full processing years must not be compared with January-July 2026 as matched windows, and no annualization is implied. The separately supplied metadata includes the fixed source-period matrix; no private clinical table or patch list is stored here.

## Disclosure and serving

Separate margins were checked jointly with existing fixed outputs and targeted complementary withholding. This is a bounded inference diagnostic, not an anonymity guarantee or proof against all external knowledge. Publisher files already expose fine activity. New revisions or new overlapping views need a fresh review. Never expose the private joint input, exact totals, blocklists or revision deltas through this adapter.

The adapter verifies both artifact hashes, caps memory and page size, and rejects overlap. The MCP wrapper additionally shares the foundation dataset work slot with existing tools. Strict argument schemas reject additional filters. This repository does not enable production, provision resources or publish datasets.
