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

## Run the example client

Python 3.10+ is required. The code-only source bundle contains the Python package, test suite and example scripts. Materialize it in the repository root before installing:

```bash
python3 bootstrap_source.py
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[build,test]'
python scripts/query_remote.py list
python scripts/query_remote.py dataset_info
python scripts/query_remote.py known_care_activity \
  --arguments '{"uf":"RJ","year":2025,"view":"residence","limit":100}'
```

On Windows, run `python bootstrap_source.py` and activate with `.venv\Scripts\activate`.

Check the returned `truncated` flag. A truncated response is not a complete list. Use municipality filters where available rather than assuming the first 100 rows are exhaustive.

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
