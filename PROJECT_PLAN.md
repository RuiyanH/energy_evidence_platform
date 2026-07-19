# Energy Market Evidence Platform

## Purpose

Build a production-style ETL and document-intelligence platform that turns messy, changing, heterogeneous evidence into reliable, traceable, testable analytical datasets.

The project is designed to demonstrate competency relevant to Data & AI Engineering roles, especially work involving imperfect source data, structured and unstructured inputs, reproducible workflows, applied AI, and defensible technical decisions.

## Core Use Case

The platform ingests public energy-market and regulatory data from several source types:

- Structured APIs for electricity prices, load, generation, and weather
- Semi-structured CSV and Excel reports whose schemas may change over time
- Regulatory filings, utility reports, market-monitoring documents, PDFs, and scans
- Revised or corrected versions of previously published files

For a selected electricity-market event, the system should:

1. Reconstruct the event timeline.
2. Identify affected markets, utilities, and regions.
3. Calculate changes in price, load, and generation.
4. Retrieve relevant supporting documents and excerpts.
5. Preserve provenance from every analytical result back to the original source and pipeline run.

## First Portfolio MVP Vertical Slice

The first build should not begin with generic "energy data." It should commit to one narrow, testable market story and expand only after that vertical slice works end to end.

Market: ERCOT Texas real-time electricity market.

Event type: Energy Emergency Alert (EEA) or grid-emergency event, starting with an EEA Level 2 or Level 3 declaration and the surrounding seven-day market window.

Use exactly three source families for the first slice:

1. ERCOT market and operations data
   - Examples: real-time settlement point prices, actual system load by weather zone, resource outage capacity, and price adders.
   - Access constraints: public ERCOT data products are available through public pages, CSV/XML/ZIP files, and API paths, but Public Data API use requires ERCOT developer registration, an ID token, and a subscription key. High-frequency extracts can be large and need throttled historical backfills.
   - Why it fits: provides interval-level price, load, and operating-condition facts for `fct_market_intervals`, freshness checks, incremental loads, duplicate interval handling, and late-arriving corrections.

2. NOAA/NWS weather evidence
   - Examples: weather alerts, observations, and extreme heat or cold context for Texas zones during the event window.
   - Access constraints: NWS API data is public but should be requested with a descriptive `User-Agent` and polite retry behavior; NOAA CDO historical data may require a free email-issued token.
   - Why it fits: gives an independent explanatory source for event drivers, supports region/date joins, and exercises API retry, rate-limit, and cross-source reconciliation behavior.

3. ERCOT, PUCT, and market-monitor event documents and notices
   - Examples: ERCOT public notices, EEA communications, PUCT Interchange filings, and Independent Market Monitor reports.
   - Access constraints: documents are public but distributed across searchable web pages, archives, PDFs, and filings. Older notices may have limited archive windows, and some PDFs may require OCR or table extraction.
   - Why it fits: exercises immutable raw storage, document versioning, citation-preserving extraction, page-level provenance, evidence search, and revised/corrected document handling.

Phase 1 should prove this slice first. PJM, CAISO, FERC-wide filings, additional utilities, and broader market comparisons are stretch goals after the ERCOT slice has passed ingestion, lineage, quality, and evidence-search acceptance tests.

## Why This Project

The goal is not merely to move clean data from an API into a dashboard. The project should demonstrate production engineering judgment through:

- Idempotent ingestion and safe reruns
- Incremental loading and historical backfills
- Schema evolution handling
- Late-arriving data
- Duplicate and revised documents
- Partial-failure recovery
- Data contracts and quality gates
- Data lineage and source provenance
- Logging, metrics, monitoring, and alerts
- CI/CD and infrastructure as code
- Secrets management and role-based access
- Responsible AI-assisted document workflows

## Proposed Architecture

### 1. Data Sources

Use at least three meaningfully different source types:

#### Structured APIs

Examples include hourly electricity prices, system load, generation mix, weather observations, and plant or utility metadata.

#### Semi-Structured Files

Use CSV or Excel reports with inconsistent names, changing columns, duplicated intervals, or missing fields.

#### Unstructured Documents

Use regulatory filings, utility reports, market-monitoring PDFs, scanned tables, and corrected document versions.

### 2. Immutable Raw Storage

Store every source exactly as received in Azure Blob Storage or an equivalent object store.

```text
raw/
  market_prices/source=<source>/year=<yyyy>/month=<mm>/
  weather/source=<source>/year=<yyyy>/month=<mm>/
  documents/source=<source>/date=<yyyy-mm-dd>/
```

Capture metadata for every object:

```text
raw_object_id
source_system
source_dataset
canonical_source_key
source_url
storage_uri
retrieved_at
source_modified_at
http_etag
content_hash_algorithm
content_hash
byte_size
mime_type
pipeline_run_id
schema_version
ingestion_status
```

Never overwrite raw inputs. Preserve every changed or corrected version.

### Raw Manifest and Revision Contracts

All raw inputs must be registered before extraction. The raw manifest is the contract that makes reruns, duplicate detection, corrected files, and lineage testable.

`raw_objects` stores byte-level identity:

```text
raw_object_id
source_system
source_dataset
canonical_source_key
source_url
storage_uri
content_hash_algorithm
content_hash
byte_size
mime_type
first_seen_at
retrieved_at
source_modified_at
http_etag
pipeline_run_id
raw_status
```

Uniqueness rules:

- `raw_object_id` is immutable.
- Same `content_hash` means identical bytes.
- Same canonical source key with a new content hash creates a new version, never an overwrite.
- Same content found at multiple URLs creates additional observations, not duplicate raw objects.
- Failed or quarantined inputs still receive manifest records so diagnosis can trace back to the retrieved bytes.

`raw_observations` stores discovery events:

```text
observation_id
raw_object_id
source_url
discovered_at
retrieved_at
source_filename
http_status
http_etag
source_modified_at
pipeline_run_id
```

Represent logical source artifacts separately from byte-level raw objects.

`source_artifacts`:

```text
artifact_id
source_system
artifact_type
canonical_source_key
title
reporting_period
market
utility
first_seen_at
```

`artifact_versions`:

```text
artifact_version_id
artifact_id
raw_object_id
version_number
content_hash
published_at
observed_at
source_modified_at
supersedes_artifact_version_id
change_type
is_current
```

Allowed `change_type` values are `duplicate`, `new`, `correction`, and `metadata_only`.

Analytical outputs must declare whether they use latest-known data or as-published/as-of data.

### 3. Orchestration

Use Apache Airflow to coordinate the pipeline:

```text
discover_sources
    -> download_and_hash
    -> validate_raw_input
    -> extract_structured_data / extract_document_content
    -> load_staging
    -> run_dbt_models
    -> run_quality_tests
    -> publish_outputs
    -> update_search_index
```

Required orchestration behaviors:

- Scheduled daily runs
- Parameterized historical backfills
- Retries with exponential backoff
- Task-level timeouts
- Failure callbacks
- Dataset-level dependencies
- Idempotent reruns
- Quarantine or dead-letter paths

Idempotency contract:

- Every pipeline task must have a deterministic idempotency key derived from source system, dataset or artifact key, logical partition or date range, raw content hash or input fingerprint, extractor/model version, and pipeline code version.
- Rerunning the same task with the same key must produce the same persisted records and must not create duplicate warehouse rows, document chunks, embeddings, or search-index entries.
- Writes must use staging tables plus atomic merge/upsert semantics.
- Partial task failures must leave either no published changes or a recoverable failed run record.
- Task state transitions must be retry-safe: discovered, downloaded, registered, extracted, staged, published, quarantined, or failed.

### 4. Python Extraction Package

Keep extraction logic in a tested Python package rather than embedding it directly in notebooks or DAG files.

```text
src/
  ingestion/
    api_client.py
    file_downloader.py
    document_discovery.py
  extraction/
    pdf_text.py
    table_extraction.py
    metadata_extraction.py
  validation/
    schemas.py
    business_rules.py
  loading/
    warehouse.py
    blob_storage.py
```

Standardize extraction outputs:

```python
from dataclasses import dataclass
from typing import Any


@dataclass
class ExtractionResult:
    source_id: str
    raw_object_id: str
    artifact_version_id: str | None
    records: list[dict[str, Any]]
    warnings: list[str]
    extraction_method: str
    confidence: float | None
    schema_version: str
    extractor_version: str
    source_locators: list[dict[str, Any]]
```

### 5. Document Processing

For every document:

1. Download it and calculate a content hash.
2. Detect exact duplicates.
3. Extract native text when available.
4. Fall back to OCR for scanned pages.
5. Extract tables separately.
6. Preserve page numbers and document coordinates.
7. Validate required metadata.
8. Quarantine failed extractions.
9. Chunk accepted documents while preserving citation metadata.
10. Optionally create embeddings and update a retrieval index.

Store provenance for every extracted unit:

```text
document_id
raw_object_id
artifact_version_id
document_version
page_number
section
extraction_method
extractor_version
text
confidence
content_hash
pipeline_run_id
source_locator
```

`source_locator` must be structured enough to re-open the original evidence: page number, bounding box when available, table number, row number, sheet name, byte offset, or source API request parameters.

### 6. Warehouse Modeling with dbt

Use PostgreSQL locally and Azure Database for PostgreSQL or Azure SQL in the deployed version.

```text
models/
  staging/
    stg_market_prices.sql
    stg_load.sql
    stg_documents.sql
    stg_document_entities.sql
  intermediate/
    int_hourly_market_conditions.sql
    int_document_event_links.sql
  marts/
    fct_market_intervals.sql
    fct_regulatory_events.sql
    dim_market.sql
    dim_market_location.sql
    dim_utility.sql
    dim_document.sql
    mart_event_impact.sql
```

Implement:

- Primary-key and uniqueness tests
- Non-null tests
- Accepted-value tests
- Referential-integrity tests
- Source freshness checks
- Custom business-rule tests
- Incremental models
- Snapshots for changing records
- Slowly changing dimensions where appropriate

Energy-market modeling requirements:

- Store all interval facts with `interval_start_utc`, `interval_end_utc`, `interval_grain_minutes`, `timezone_name`, `local_date`, `local_interval_start`, `utc_offset_minutes`, and `is_dst`.
- Treat UTC timestamps as the analytical join key. Local timestamps are derived attributes used for reporting and source reconciliation, never the sole primary key.
- Support DST transition days explicitly: local operating days may contain 23, 24, or 25 hourly intervals, and repeated local hours must remain distinguishable by UTC offset.
- Preserve source interval labels such as hour-ending, market day, operating day, and settlement interval when provided.
- Model market locations in an effective-dated `dim_market_location` with `source_system`, `source_location_id`, `canonical_location_id`, `location_name`, `location_type`, `timezone_name`, `parent_zone_id`, `valid_from`, `valid_to`, and `is_current`.
- Preserve record-level revision metadata: `published_at`, `source_modified_at`, `retrieved_at`, `market_run`, `settlement_run`, `revision_number`, `valid_from`, `valid_to`, and `is_current`.
- Keep both source and normalized measurement fields: `value`, `source_unit`, `normalized_value`, `normalized_unit`, `currency`, and `unit_conversion_method`.
- Use canonical normalized units such as `USD/MWh` for prices, `MW` for load and generation capacity or power, `MWh` for interval energy, and documented converted units for weather data.

Energy-specific dbt tests:

- Intervals have non-null UTC start/end timestamps, positive duration, and duration matching `interval_grain_minutes`.
- No duplicate current facts exist for the same source, location, market run, settlement run, measurement type, interval start UTC, and revision.
- Local time fields must be derivable from UTC timestamp plus IANA timezone.
- DST transition fixtures must produce valid 23-hour and 25-hour local operating days without dropped or merged intervals.
- Market facts must reference a valid effective-dated market location for the interval timestamp.
- Exactly one current record exists per revised logical fact; superseded revisions remain queryable for as-of analysis.
- Settlement and market-run values use accepted values, for example `day_ahead`, `real_time`, `preliminary`, `final`, and `corrected`.
- Units and currencies use accepted values; price, load, generation, and weather measures cannot mix incompatible units.
- Aggregations from subhourly to hourly/daily grain use documented rules: sums for energy, averages or duration-weighted averages for prices and power as appropriate.

End-to-end lineage requirements:

- Every staging row must include `raw_object_id`, `artifact_version_id` when applicable, `source_record_key`, `source_locator`, `extraction_run_id`, `extractor_version`, and `schema_version`.
- Every mart row must include `build_run_id`, `model_version`, `input_fingerprint`, and `provenance_set_id`.
- `provenance_edges` must map final outputs back to source inputs with `downstream_asset_type`, `downstream_asset_id`, `upstream_asset_type`, `upstream_asset_id`, `contribution_type`, and `locator`.
- Search chunks, embeddings, index entries, and dashboard outputs must use the same provenance IDs as warehouse marts.

Affected-asset reprocessing requirements:

- Maintain `asset_builds` with `asset_key`, `asset_type`, `input_fingerprint`, `code_version`, `pipeline_run_id`, `build_status`, and `built_at`.
- Maintain `asset_dependencies` with `downstream_asset_key`, `upstream_asset_key`, and `dependency_type`.
- When a raw object, artifact version, extractor version, schema version, or dbt model version changes, compute affected downstream assets by comparing input fingerprints.
- Rebuild only assets whose fingerprint changed, plus declared lookback windows for late-arriving interval data.

### 7. Failure Scenarios

Create fixtures that intentionally simulate:

- HTTP 429 responses
- Valid JSON with missing required fields
- Source column renaming
- Duplicated time intervals
- Corrected PDFs replacing earlier versions
- Different filenames containing identical content
- OCR returning empty output
- Impossible publication dates
- Late-arriving data that changes prior aggregates
- Database failure halfway through a batch
- DST spring-forward and fall-back days with missing and repeated local hours
- Mixed five-minute and hourly market intervals for the same date range
- Node or zone rename with the same source identifier changing meaning over time
- Corrected settlement data that supersedes but does not delete an earlier published value
- Source file using unexpected units or currency

Expected system behavior:

- Retry transient failures.
- Reject invalid contracts.
- Quarantine malformed inputs.
- Prevent duplicate loads.
- Roll back incomplete writes.
- Reprocess only affected downstream assets.
- Alert after final retry failure.
- Preserve failed inputs for investigation.
- Record warnings and assumptions in audit tables.

Document diagnosis and recovery steps in `docs/incident_playbook.md`.

### 8. Data Quality

Create a `data_quality_results` table:

```text
check_name
dataset
run_id
severity
status
observed_value
expected_value
failed_record_count
executed_at
```

Organize checks into:

- Contract checks
- Integrity checks
- Completeness checks
- Plausibility checks
- Reconciliation checks
- Freshness checks

Define publication behavior by severity:

```text
warning  -> publish with a visible warning
error    -> block the affected dataset
critical -> stop publication and alert
```

### 9. Observability

Track metrics including:

- Rows ingested
- Documents discovered
- Documents successfully extracted
- Quarantined inputs
- Duplicate rate
- Source-to-publish latency
- Data-test failure rate
- Retry count
- Extraction confidence
- Cost per run
- Latest successful publication time

Use structured logs:

```text
timestamp
run_id
task_id
source
dataset
record_count
duration_ms
status
error_type
```

Create alerts for:

- Pipeline failure
- Freshness violations
- Unexpected record-count changes
- High extraction-failure rates
- Missing expected sources
- Excessive run duration

### 10. Security

Even when using public data, design the platform as though restricted data could be introduced later.

Demonstrate:

- Secrets in Azure Key Vault
- Managed identities or service principals
- Separate development and production configuration
- Role-based access control
- Read-only application credentials
- Secret scanning
- Logs that avoid sensitive document content
- A synthetic restricted dataset available only to a privileged role

Add `docs/security_model.md` with a lightweight threat model covering source documents, credentials, AI-processing inputs, and access boundaries.

### 11. CI/CD

On every pull request:

- Run Ruff
- Check formatting
- Run static type checking
- Run unit tests
- Run integration tests against temporary PostgreSQL
- Validate Airflow DAG imports
- Run `dbt compile`
- Run dbt tests against fixture data
- Run energy-time fixture tests for DST, interval grain, revisions, and unit conversions
- Run evidence-search evaluation on fixture documents
- Validate source catalog, schema contracts, and manifest table migrations
- Build Docker images
- Scan for committed secrets

On merge:

- Build a versioned image
- Apply infrastructure or application changes
- Run database migrations
- Execute smoke tests
- Roll back when health checks fail

### 12. Infrastructure as Code

Use Terraform or Bicep to provision:

- Azure Blob Storage
- Managed PostgreSQL or Azure SQL
- Azure Key Vault
- Container runtime
- Application Insights and Log Analytics
- Role assignments
- Networking and firewall rules

A reviewer should be able to deploy the platform through a small number of documented commands.

## User-Facing Product

Build a lightweight Streamlit application or FastAPI service with three primary surfaces.

### Pipeline Health

Show:

- Last successful run
- Source freshness
- Records processed
- Quarantined inputs
- Failed quality checks
- Recent incidents

### Market Event Analysis

Allow users to choose a region, date range, and event. Display:

- Price and load changes
- Generation mix
- Before-and-after comparisons
- Relevant regulatory documents
- Data-quality warnings

### Evidence Search

Allow users to ask questions such as:

> What factors were cited as contributing to this market event?

Return evidence with:

- Document title
- Publication date
- Page number
- Document version
- Extraction method
- Source citation
- Confidence warnings

The AI layer must sit downstream of the validated ETL system and must not conceal provenance or extraction uncertainty.

### Evidence Search Evaluation Contract

Maintain a version-controlled evaluation set for document intelligence and retrieval. Each case should include the user question, answerability label, expected event/region/date scope, gold document IDs, document versions, page numbers, and supporting text spans.

Include at least:

- 25 answerable evidence questions across several market events
- 10 unanswerable or out-of-scope questions
- 5 versioning cases where corrected documents supersede earlier versions
- 5 OCR or scanned-document cases
- 5 alias/entity cases for utilities, regions, market operators, or filing names

Retrieval acceptance criteria:

- For answerable questions, at least one gold supporting chunk appears in the top 5 results for 90% of evaluation cases.
- All required supporting evidence appears in the top 10 results for 80% of multi-document cases.
- Metadata filters for region, date range, document version, and source type return zero out-of-scope documents in fixture tests.
- Duplicate documents are collapsed by content hash, while corrected versions remain separately retrievable.
- Quarantined or failed-extraction documents never appear in search results.

Citation acceptance criteria:

- Every generated answer contains at least one citation per factual claim.
- Every citation includes document title, document ID, version, page number, extraction method, content hash or source URL, and pipeline run ID.
- Cited spans must contain supporting evidence for the claim in at least 85% of manually reviewed evaluation cases.
- Citation metadata must round-trip to the stored raw document and extracted page text for 100% of automated fixture cases.
- Low-OCR-confidence citations are allowed only with a visible confidence warning.

No-answer acceptance criteria:

- For unanswerable questions, the system must say that the evidence corpus does not support an answer instead of generating an unsupported explanation.
- No-answer precision should be at least 90% on the negative evaluation set.
- Nearby documents may be returned only under a separate "possibly related evidence" label.
- The system must not cite documents that do not directly support the answer.

Confidence behavior:

- Separate extraction confidence, retrieval score, and answer confidence.
- Answer confidence should be derived from evidence coverage, citation quality, extraction confidence, and whether multiple independent sources agree.
- Answers below the configured confidence threshold must show a warning or abstain.
- Confidence thresholds and observed evaluation metrics should be recorded in CI artifacts or an evaluation report.

CI gate:

- Run the evidence-search evaluation on fixture documents in CI.
- Block merge if citation metadata fails, quarantined documents appear in results, no-answer tests regress, or top-k retrieval metrics fall below threshold.

## Scope Target

A credible MVP version should include:

- The ERCOT EEA vertical slice above
- 3 source families
- 1 to 3 event windows
- 30 to 100 documents
- 100,000 to 1,000,000 interval-level records
- Daily incremental runs
- At least one historical backfill
- At least 10 deliberate failure scenarios
- Approximately 25 automated tests

A fuller portfolio version can then expand to approximately:

- 5 to 10 structured sources
- 500 to 2,000 documents
- Several million interval-level records
- Daily incremental runs
- At least one historical backfill
- At least 15 deliberate failure scenarios
- Approximately 50 automated tests

Production quality should be demonstrated through reliability and engineering discipline rather than raw data volume.

## Repository Structure

```text
energy-evidence-platform/
├── airflow/
│   └── dags/
├── dbt/
│   ├── models/
│   ├── snapshots/
│   └── tests/
├── contracts/
│   ├── sources/
│   └── schemas/
├── evaluation/
│   └── evidence_search/
├── src/
│   ├── ingestion/
│   ├── extraction/
│   ├── validation/
│   └── loading/
├── api/
├── dashboard/
├── infrastructure/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── failure_scenarios/
├── docs/
│   ├── architecture.md
│   ├── data_lineage.md
│   ├── data_dictionary.md
│   ├── security_model.md
│   ├── incident_playbook.md
│   └── design_decisions/
├── .github/workflows/
├── docker-compose.yml
├── Makefile
└── README.md
```

## Architecture Decision Records

Document decisions including:

- Airflow versus Azure Data Factory
- ELT for structured records versus preprocessing for documents
- Representation of revised source files
- Idempotency and retry safety
- Canonical time, interval grain, market-location identity, revision, settlement, and unit semantics for energy-market facts
- Quality gates that block publication
- Rules for sending data to external AI models
- Relational warehouse plus document index

## Demonstration Video

Create a five-minute walkthrough showing:

1. A healthy scheduled pipeline.
2. A new source file arriving.
3. The immutable raw object and metadata.
4. Transformation and quality tests.
5. Publication into the analytical mart.
6. A deliberately malformed source.
7. Quarantine rather than production corruption.
8. A monitoring alert.
9. Repair and historical reprocessing.
10. An analytical result traced to the original document and page.

## Development Sequence

### Phase 1: Walking Skeleton

Build the ERCOT EEA vertical slice through:

```text
ingestion -> raw storage -> staging -> dbt mart -> dashboard
```

Phase 1 must include the raw manifest, artifact-version model, deterministic idempotency keys, UTC interval semantics, and one provenance-backed dashboard result. Deploy the smallest end-to-end version early.

### Phase 2: Reliability

Add:

- Idempotency hardening across every source and derived asset
- Incremental loads
- Backfills
- Retries
- Quarantine
- Audit logging
- Data contracts

### Phase 3: Production Engineering

Add:

- Unit and integration tests
- CI/CD
- Infrastructure as code
- Secrets management
- Monitoring and alerts

### Phase 4: Document Intelligence

Add:

- Extraction fallbacks
- Document-versioning edge cases and corrected-PDF handling
- Entity extraction
- Page-level provenance
- Evaluated evidence search and optional RAG

### Phase 5: Failure and Recovery Demonstration

Implement controlled failure cases, incident documentation, and recovery procedures.

## Potential Resume Bullets

- Architected and deployed an Azure-based data platform ingesting energy-market data, heterogeneous reports, and scanned regulatory documents through scheduled Airflow workflows, immutable object storage, PostgreSQL, and dbt analytical models.
- Implemented incremental and idempotent loading, document versioning, schema-evolution handling, historical backfills, quarantine workflows, and more than 50 automated data-quality and integration tests.
- Built CI/CD and infrastructure-as-code workflows covering container deployment, database migrations, DAG validation, dbt testing, secret management, role-based access, monitoring, and failure alerts.
- Developed a citation-preserving retrieval service linking analytical findings and AI-generated summaries to source version, page, extraction method, and pipeline run.

## Project Story

The central message of the project should be:

> I designed a system that makes imperfect, changing, document-heavy evidence reliable, traceable, testable, and usable under real operational constraints.
