# SUS healthcare MCP

Ask questions about Brazil's public healthcare data from an MCP client: hospital and outpatient activity, facility capacity, mortality, and selected rare-disease billing patterns.

This is a read-only, fixed-vintage analytical service. It returns reviewed aggregate views, not patient records.

## Use the hosted MCP

Add this **Streamable HTTP** server URL to an MCP client that supports remote servers:

```text
https://sus-health-mcp.fly.dev/mcp
```

No API key is required. Start with `dataset_info`, then `dataset_coverage` to check the scope and warnings before interpreting results. The public instance limits traffic to 40 HTTP requests per minute per client IP.

Example questions:

- Which municipalities have visible E85.1 / tafamidis 20 mg billing in 2025?
- Where is billing recorded outside the municipality of residence?
- What registered SUS bed capacity is available in a reviewed CNES snapshot?

Questions are translated into the fixed tools below by your MCP client. The server does not offer arbitrary SQL or every possible drug filter.

| Tool | What it returns |
| --- | --- |
| `dataset_info` | Serving scope, vintages and limitations |
| `dataset_coverage` | Reviewed periods and source gaps |
| `facility_capacity` | CNES beds, facility types, services and authorizations |
| `geographic_signals` | Annual municipality/CID record intervals |
| `known_care_activity` | Reviewed E85.1 billing and residence-to-billing municipality flows |
| `rare_disease_billing` | Related E85 codes, tafamidis 61 mg, and separate nonspecific workup billing views |
| `reference_lookup` | Dated code/name lookup; ambiguous matches are listed |
| `reference_resolve` | Exact dated/auxiliary/unmapped code labels |
| `released_cells_page` | Cursor-bound complete retrieval of existing visible cells |
| `research_methods` | Query-specific units, time basis, sources and limitations |
| `foundation_coverage` | Reference vintages and frozen source coverage |

## Run the example client

Python 3.10+ is required. Clone this repository, then install the Python package and example scripts:

```bash
git clone https://github.com/bnovarini/sus-health-mcp.git
cd sus-health-mcp
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[build,test]'
python scripts/query_remote.py list
python scripts/query_remote.py dataset_info
python scripts/query_remote.py known_care_activity \
  --arguments '{"uf":"RJ","year":2025,"view":"residence","limit":100}'
```

On Windows, activate with `.venv\Scripts\activate`.

Check the returned `truncated` flag. A truncated response is not a complete list. Use `released_cells_page` and follow `next_cursor` until null for complete retrieval of the existing visible lattice. Missing cells remain unknown, not zero. Complete file exports are owner-only; no public file-download route exists. See [FOUNDATION.md](FOUNDATION.md) for reference sources, self-hosting and residual bulk-access risk.

## Local setup without real data

The repository includes **no data artifacts**, credentials, raw health files or usage logs. The following creates a clearly labeled fictional registry fixture so you can test the serving code:

```bash
python scripts/create_demo.py
SUS_STAGED_DATA=data/demo SUS_USAGE_DB=/tmp/sus-usage.db \
  python -m sus_health_mcp --http
```

In another terminal, using the same virtual environment:

```bash
curl http://localhost:8080/healthz
python scripts/query_remote.py dataset_info --url http://localhost:8080/mcp
python scripts/query_remote.py facility_capacity --url http://localhost:8080/mcp \
  --arguments '{"uf":"SP","year":2024,"month":1,"family":"LT"}'
python -m pytest -q
```

The demo exposes only registry tools. Its one row is fictional and cannot reproduce the hosted results.

## Self-hosting reviewed artifacts

Real-data self-hosting needs separately built and reviewed artifacts. They are not downloadable from this repository. Copy only reviewed serving artifacts into the following directories:

| Environment variable | Required files |
| --- | --- |
| `SUS_STAGED_DATA` | `capacity.parquet`, `metadata.json` |
| `SUS_CLINICAL_DATA` | `clinical.parquet`, `clinical-metadata.json` |
| `SUS_KNOWN_CARE_DATA` | `known-care.json`, `known-care-metadata.json` |
| `SUS_DEEPER_DATA` | `surface-intervals.json`, `metadata.json` |

Enable the additional fixed tools with `SUS_ENABLE_CLINICAL_2024=true`, `SUS_ENABLE_KNOWN_CARE=true`, and `SUS_ENABLE_DEEPER=true`. The historical `CLINICAL_2024` flag name is retained, but the metadata defines the actual years. Hash checks reject altered artifacts. Period gates reject unverified registry periods.

The Dockerfile installs the code only. Mount reviewed registry artifacts at `/data/staged` and set the other paths and activation flags as needed. The default HTTP host allowlist is the hosted domain plus localhost and 127.0.0.1; review `staged_server.py` before serving under another domain. Do not disable host validation to work around deployment errors.

The ingestion code in `src/sus_health_mcp/build.py` can inventory and aggregate publisher files. Ingestion is **not** a one-command reproduction of the reviewed hosted release: reconciliation, dated code checks and joint disclosure review are separate steps. Experimental modules are retained for inspection; `staged_server.py` is the serving implementation used here.

## Data scope

Snapshot checked on 14 October 2026. Always consult the live metadata for the current scope.

- SIH RD, SIA PA and AM: 2022-2025 full processing-file years; January-July 2026 partial.
- CNES ST, LT, SR and HB: 2022-2025 monthly snapshots; January-August 2026 partial. SR/AP August 2024 remains unavailable.
- SIM: 2022-2024 stable; full-year 2025 preliminary; January-August 2026 preview. SIM is national mortality data, not SUS-only, and follows death year.
- SINASC, SINAN and person linkage are out of scope.

SIH source totals do not exactly match publisher morbidity AIH totals. The differences match principal CID codes absent from the current auxiliary dictionary, but the publisher conversion has not been independently confirmed. AM matching independent publisher totals also remain unverified. Neither issue was "fixed" by dropping or changing source rows. Missing source periods are reported as gaps, not zero activity.

## Reading the results

Clinical and billing views use a 20-record minimum, width-10 intervals, targeted withholding and Federal District exclusion. These controls do not guarantee anonymity or 20 distinct people. One person can generate repeated billing records.

- Records are not patients, prevalence, diagnoses or untreated need.
- Unmarked or absent cells are unknown, not zero.
- Billing-provider municipality is not a confirmed clinical hospital or proof of patient travel.
- Registered capacity is not occupancy, appointment availability or a disease-specific service guarantee.
- Changes across years can reflect coding and reporting, not disease growth.
- No patient-finding yield, cost saving or clinical risk score has been validated.

Source families come from DATASUS. This project is not affiliated with DATASUS or Brazil's Ministry of Health. Data licensing and publisher terms are separate from the code license.

## Development

The packaged unit tests use synthetic fixtures. Hosted-artifact integration checks are deliberately excluded because their data files are not distributed. No automatic vintage replacement is performed by the serving code.

The older `bootstrap_source.py` file is a legacy copy of the same source. It is not needed for setup; use the normal `src/`, `tests/` and `scripts/` tree.

## Fixed state activity

The optional `state_activity_page` and `state_activity_methods` tools add separate annual residence-UF CID and procedure source-record intervals. Read [STATE_ACTIVITY.md](STATE_ACTIVITY.md) for scope, units and limits. Set both `SUS_FOUNDATION_DATA` and `SUS_STATE_DATA` to separately supplied frozen artifacts. This repository contains only code and synthetic tests, not clinical data or private disclosure-review material.

## Annual series and population context

Optional `annual_activity_series` and `annual_series_methods` compose existing frozen state intervals with a stated population vintage. See [ANNUAL_SERIES.md](ANNUAL_SERIES.md). Set `SUS_SERIES_DATA` alongside the state/foundation artifact directories. No population workbook or clinical data is bundled here.

## Provider activity and administrative catchments

The hosted service now has 17 tools. `provider_activity_methods` describes the fixed release; `provider_activity_page` returns separate provider-CID, provider-procedure or residence-UF interval margins. Exact establishment and provider municipality are required. No joint filters or exact totals.

Read [PROVIDER_ACTIVITY.md](PROVIDER_ACTIVITY.md) for coverage, billing-record units, dated-registration identity limits and disclosure caveats. The tested known-support model adds no new or stronger small-cell positive bound, but 633 positive bounds already implied by earlier releases remain unchanged. This is not a general privacy guarantee or evidence of patient identification.

## Reference reimbursement and registered-capacity context

The hosted service has 19 tools. `reimbursement_reference` returns dated separate SIGTAP SH/SA/SP reference components, not actual payments or prices. `provider_activity_context` places unchanged annual provider-procedure record intervals beside an explicitly chosen monthly CNES snapshot and that month's reference. See [REFERENCE_CONTEXT.md](REFERENCE_CONTEXT.md). No ratios, utilization/shortage scores, rankings, payment multiplication or new clinical cells are introduced. Annual records are not assumed to fall in the selected month; missing is unknown, not zero.




## Data revisions



- 17 October 2026: DATASUS re-published the SIH RD processing files for September 2025 through July 2026. The hosted RD2025 and RD2026 tables were re-anchored to the re-released files (net +91,269 source records; RD2026 loses 75 released cells that fell under the 20-record minimum). Earlier published RD2025/RD2026 intervals are superseded. Current release IDs: `clinical-2022-2026-SIMpreviews-20261017-rdrepub`, `phase2-state-record-margins-20261017-rdrepub`, `phase4-provider-20261017-rdrepub`, `registry-fixed2022-2026partial-20261017-rdrepub`.
