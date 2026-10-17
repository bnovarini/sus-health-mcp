# Fixed provider activity

Two tools supplement the existing 15 tools:

- `provider_activity_methods`: scope, source coverage, units and caveats. Read first.
- `provider_activity_page`: one fixed family/year, seven-digit source establishment code and six-digit provider municipality, then one separate CID, procedure or residence-UF margin. Optional exact code and bound pagination cursor; at most 100 rows.

The fixed release has 45 tables and 7,076,409 visible interval rows. It covers RD, PA and AM for 2022-2025 and January-July 2026 processing files. These are source records, not unique people, deduplicated admissions, approved quantities, prescriptions or doses. PA quantities must not be inferred from record counts. AM units remain limited to source-record semantics pending independent reconciliation.

CID and procedure margins retain all source residences. Catchments use valid frozen December 2024 residence-UF codes only, excluding DF and unknown residence. Provider scope excludes DF and municipalities outside that frozen catalog. Missing, suppressed and withheld rows are unknown, not zero. Later municipalities outside the catalog are not necessarily invalid. Residence-UF codes are two-digit numeric state codes, not abbreviations.

Establishment code plus provider municipality is a billing identity, not proof of historical hospital, legal entity, service line or clinical site. A dated CNES ST match is a registration observation, not active capacity. Current names do not prove historical names. Administrative catchments are not referrals, patient journeys, markets or treatment need.

## Disclosure limits

Records below 20 are omitted. Visible counts use outward ten-wide integer intervals. Additional targeted withholding addresses demonstrated complementary inference in a known-support interval-propagation diagnostic against existing state/municipal CID, state procedure, and applicable fixed known-care/deeper releases. Annual series reuse state intervals; CNES adds no clinical-count constraint.

Across all 15 family/year groups and 3,380,117,376 source records, the tested combined model adds no new or stronger positive lower bound on under-20 joint cells after withholding. Existing outputs alone still imply 633 positive lower bounds, with no positive exact counts in that diagnostic. The existing bounds were explicitly retained rather than silently changing earlier releases. This is not a general privacy guarantee, a general reconstruction proof or evidence of patient identification.

No joint filters, prefixes, arbitrary totals, demographic strata, pooled years/families or inferred zeros are offered. Literal billing placeholders such as CID 0000 are retained, not validated as clinical diagnoses.

## Runtime and reproducibility

Enable with `SUS_ENABLE_PROVIDER=true` and set `SUS_PROVIDER_DATA` to a directory containing `candidate-metadata.json` and `candidate/*.parquet`. No data ships in this repository. Metadata lists artifact SHA256 hashes, source coverage and fixed scope. Import verifies the exact artifact bytes. The expensive query uses the existing process-wide work slot plus a local guard. It does not add serving capacity.

Review tests cover artifact hashes, unique keys, raw intervals, reviewed-withholding absence, pagination/cursor binding, strict native/HTTP inputs, busy rejection and regression. Local combined peak was 595.5 MiB under the existing 1 GB configuration. This is a test observation, not a future memory guarantee.
