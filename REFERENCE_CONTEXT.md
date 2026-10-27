# SUS reference values and registered-capacity context

`reimbursement_reference(procedure,vintage)` requires an exact ten-digit procedure and explicit YYYYMM vintage. It returns separate national SH, SA and SP reference components as integer centavos and two-decimal BRL strings, financing labels and dated modality/instrument/service/bed relations. The fixed artifact covers January 2022-October 2026 (58 monthly vintages). The September and October 2026 publisher tables were added on 27 October; the prior 56 vintages were preserved unchanged. The fixed reference contains 279,932 procedure-month rows and 1,330,130 dated procedure-relation rows. No reference database ships in this code repository.

`provider_activity_context` requires family, processing-file year, exact source establishment and provider municipality, exact procedure, snapshot month and one registry family (ST/LT/SR/HB). It displays the unchanged released annual provider-procedure record interval beside the explicitly selected same-year monthly CNES rows and same-month SIGTAP reference. Registry pagination binds its scope and source hash.

## Interpretation limits

- This is side-by-side context, not a capacity utilization or mismatch metric. Annual processing-file records are not assigned to the chosen snapshot month or a clinical service date.
- No ratios, bed-days, tariff multiplication, payment estimate, shortage score, ranking, service-line inference or clinical cross-filter. Source billing records are not patients, admissions or approved quantities.
- National reference components are not actual payment, economic cost, private prices or full funding. Conditional increments, local complements and billing eligibility are not computed. Zero component does not mean no funding. Missing code/vintage is unknown, not zero.
- LT quantity/SUS beds are registered beds, not occupancy or disease-specific available capacity. CNES TP_LEITO:CODLEITO and SIGTAP bed-type codes are separate namespaces.
- ST/SR/HB quantities count registry rows, not throughput, staffing, sessions or beds. Administrative compatibility is not proof of service provision. Different source SUS flags have different meanings.
- Exact establishment and municipality only, no fuzzy historical-name joins, fallback location or assumed historical legal identity. Absent snapshot rows do not prove no capacity.
- 2026 activity is January-July only; an August reference snapshot does not annualize it.

## Data and checks

The fixed reference contains 279,932 procedure-month rows in 58 vintages and 1,330,130 dated relations (checked 27 October 2026). All raw monetary fields were checked against each archive's own TXT layout and an independent end-relative decoder. The official bundled XLS specifies two decimals, but its ten-character offsets are stale after the June 2025 expansion to twelve characters. TXT layouts govern positions; raw fields are preserved. No floating-point money arithmetic.

This adds no clinical cells or precision. Changing registry family/month or tariff values never conditions the clinical count: the exact same released provider-procedure interval is returned. Earlier withholding and the documented 633 pre-existing positive small-cell bounds remain unchanged. This is not a general privacy guarantee or evidence of patient identification.

Four private reader/context tests, complete registry pagination/source equality, strict native/HTTP inputs, process-wide busy rejection and all-17-existing-response regression passed. Combined local process peak was 589.7 MiB on the existing 1 GB configuration, not a future memory guarantee.

Enable `SUS_ENABLE_CONTEXT=true`, set `SUS_TARIFF_DATA` to the frozen reference directory, and enable the separately supplied provider/foundation/capacity artifacts. Artifact hashes are checked. Expensive context queries share the existing process-wide work slot. There is no automatic update or extra serving resource.

Official semantics: https://wiki.datasus.gov.br/sigtap/index.php/Procedimento and https://wiki.saude.gov.br/cnes/index.php/Pain%C3%A9is_ElastiCNES . Archive-specific URLs/hashes belong in the supplied reference metadata, not a private-data download in this repository.

## Latest reference update

The September and October 2026 tables were parsed from the DATASUS publisher archives `TabelaUnificada_202609_v2610261311.zip` and `TabelaUnificada_202610_v2610261600.zip`. The archive-specific URLs and hashes are preserved with the release record; the data archives themselves are not included in this code repository. The September table has 5,024 procedures and the October table has 5,041. Comparisons described in the private review are adjacent-month comparisons, not a full before/after comparison against superseded archive versions.

Publisher directory: [DATASUS TUP downloads](ftp://ftp2.datasus.gov.br/pub/sistemas/tup/downloads/)
