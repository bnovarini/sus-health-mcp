# Phase 1 reference and retrieval layer

The hosted service adds five tools: `reference_lookup`, `reference_resolve`, `released_cells_page`, `research_methods` and `foundation_coverage`. Existing six tool results and artifact hashes are unchanged. The code includes strict discriminated query schemas and a shared nonblocking dataset-work slot. A busy request gets a retry error rather than starting another memory-heavy scan.

## Reference provenance

The reference database is not included in git. Activated database SHA256: `01ffb2b150486b13251c486705c65821b21fbaa45de9099d753497e5dc8dacc2`. It contains 56 monthly SIGTAP dictionaries from January 2022 through August 2026, downloaded on October 16, 2026; SIH auxiliary CID labels; CNES facility and code namespaces; and current IBGE municipality names. The hash, source URLs and exact vintages belong in `reference-metadata.json` alongside the database. Lookup distinguishes dated matches, auxiliary labels and unmapped source strings. Never drop or recode a source record because its label is missing. A current facility name is not proof of historical identity or current availability.

Official sources:
- ftp://ftp2.datasus.gov.br/pub/sistemas/tup/downloads/
- ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Auxiliar/TAB_SIH.zip
- ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Auxiliar/TAB_CNES.zip
- https://servicodados.ibge.gov.br/api/v1/localidades/municipios

The residence catalog remains the original frozen December 2024 catalog. Current names are labels, not replacement geography. The publisher archive's fixed-width text and layout reproduce that catalog; its DBF/CSV tables are not interchangeable:
ftp://ftp.datasus.gov.br/territorio/tabelas/2024/12-base%20territorial_dez24.zip

## Self-hosting

Set `SUS_FOUNDATION_DATA` to a directory containing `reference-compact.sqlite`, `reference-metadata.json` and `serving-coverage-scientific.json`. The reference metadata records the database filename and SHA256. The scientific coverage snapshot must describe exactly the same frozen serving files configured by the existing data environment variables. It must not contain credentials, identifiers or permission claims. Without `SUS_FOUNDATION_DATA`, the existing registry demo remains usable and the five new tools are not registered.

The layer does not download source data on startup. It validates artifact hashes and period gates. Reference and query tests in the public tree use fictional fixtures only. Large state-wide registry pages can take longer than municipality-filtered pages. Query schemas require an explicit state, year, family and, for registry data, month; there is no arbitrary SQL or unbounded all-history query.

## Retrieval and owner-only export

`released_cells_page` returns at most 100 frozen visible cells with a query- and artifact-bound cursor. Continue until `next_cursor` is null. Complete retrieval means complete for that visible lattice, not complete source coverage or a population count. The local Python export adapter writes JSONL and a methods/hash manifest with owner-only file permissions and refuses to overwrite an existing destination. There is no public file-download endpoint.

Pagination makes collecting already-visible cells easier. It does not provide anonymity or a sub-20 secrecy guarantee. Public publisher files and other releases can enable linkage and inference. Existing targeted withholding, fixed intervals and missing-as-unknown behavior remain; they do not eliminate residual risk. Counts are administrative or billing source records, never unique people, prevalence, clinical comorbidity or causation. CNES rows describe registered capacity, not appointments or occupancy.

## Deployment validation

On October 16, 2026, the integrated service passed exact before/after response comparison for all six existing tools. All five new tools, cursor continuation and health passed live smoke tests. Shared-work-slot rejection/recovery and the integrated HTTP app passed locally; the combined test peaked at about 591 MiB. Deployment changed only the image on the existing shared CPU / 1 GiB machine, retaining the existing usage volume, routes and startup. These checks are not a claim that every possible query has been benchmarked.
