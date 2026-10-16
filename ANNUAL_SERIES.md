# Annual activity series

Call `annual_series_methods` before interpretation. `annual_activity_series` composes already-visible fixed state intervals. It introduces no new clinical extraction, exact totals, patient linkage, code groups or year sums.

## Scope

One exact `code`, one residence `uf`, one source `family` (`RD`, `PA`, `AM`) and one `kind` (`cid` or `procedure`). `years` holds one to five distinct processing-file years, 2022-2026; default 2022-2025. DF and unknown residence remain excluded, not zero. Extra filters and prefix expressions are rejected. Separate years are separate administrative cohorts, not patient trajectories.

Set `SUS_SERIES_DATA` to the separately supplied frozen population context, source-period matrix and hash manifest. `SUS_STATE_DATA` and `SUS_FOUNDATION_DATA` are also needed. No dataset or population workbook is distributed in this repository. Import starts no listener. The optional registration preserves the demo when those directories are absent.

## Units and comparisons

Original integer count bounds are unchanged. Full-year visible cells can include an outward-rounded interval of administrative source records per 100,000 total residents. Both rate bounds round outward to 0.001; this transformation cannot narrow the original count interval. It is not disease prevalence, incidence, unique people or a resident's probability of using SUS. RD administrative records, PA billing records and AM APAC records have different units. AM records are not doses or dispensing.

Missing points remain unknown and have no rate. January-July 2026 has no annual rate and is never annualized. Placeholder/non-CID-format strings get no diagnosis rate. No automatic growth/decline labels, exact deltas, interpolation, cumulative totals, rankings or code pooling are provided.

`same_processing_window` and `all_expected_billing_file_slots_present` report only those narrow properties. Neither means unbiased or complete clinical ascertainment. See [STATE_ACTIVITY.md](STATE_ACTIVITY.md) for missing AM files in every included year, RD2026 gaps and cross-state residence effects. The SIA2025 coding-notice warning remains, not an empirically measured or corrected break. PA missing residence/CID and independent publisher-reconciliation limits remain.

## Population vintage

All years use one stated IBGE revision2024 implicit-indicators workbook, July1 total resident populations. The 2022 value is a demographic reconstruction, not raw census enumeration; 2023 onward is projected. This is a coherent vintage, not a claim to use the latest annual estimate. The denominator is total residents, not the SUS-covered population. Check source URL/hash and vintage in results.

https://ftp.ibge.gov.br/Projecao_da_Populacao/Projecao_da_Populacao_2024/projecoes_2024_tab4_indicadores.xlsx

https://ftp.ibge.gov.br/Projecao_da_Populacao/Projecao_da_Populacao_2024/Serie_Relatorios_Metotodologicos_v40_Projecoes_da_Populacao_Brasil_e_Unidades_da_Federacao_Revisao_2024_3a_Edicao.pdf

Population projection boundaries and the frozen December2024 clinical municipality membership need not match exactly. The 2025 annual-estimate bulletin notes a 67-person PR/SC difference from the projection because of an interstate boundary change. Do not silently splice those annual-estimate values into this fixed projection series or redraw clinical geography.

## Serving and disclosure

The entire series occupies the existing shared dataset work slot. Context hashes and source-artifact hashes are checked. No new overlapping clinical constraint is disclosed: rates derive only from existing released intervals and public denominators. Existing disclosure limitations still apply; thresholding and aggregation do not certify anonymity. New revisions or overlapping views need their own review.
