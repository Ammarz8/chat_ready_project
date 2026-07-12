# Car Data Pipeline ETL Engine

An enterprise-grade, containerized ETL data pipeline that extracts vehicle specification data from the API Ninjas Cars API, stores the raw JSON responses in a source database (Bronze/Landing layer), flattens and normalizes the data into a relational database model (Silver/Normalized layer), and exposes an interactive CLI application for users to query and analyze the data.

---

## 1. Project Architecture

The project implements a classic **Bronze-to-Silver Lakehouse Ingestion Pattern** built on clean modular design principles:

```text
       ┌────────────────────────┐
       │   API Ninjas Cars API  │
       └───────────┬────────────┘
                   │ HTTPS GET (X-Api-Key Header)
                   ▼
       ┌────────────────────────┐
       │   Extractor Container  │
       └───────────┬────────────┘
                   │ SQL INSERT (Raw JSONB Payload)
                   ▼
 ┌──────────────────────────────────┐
 │ source_db Container (Bronze DB)  │
 └─────────────────┬────────────────┘
                   │
                   │ SQL SELECT (Raw Ingested Records)
                   ▼
       ┌────────────────────────┐
       │ Transformer Container  │
       └───────────┬────────────┘
                   │ SQL INSERT (Cleaned, Joined & UPSERTed)
                   ▼
 ┌──────────────────────────────────┐
 │ target_db Container (Silver DB)  │
 └─────────────────┬────────────────┘
                   │
                   │ SQL SELECT (Analytical Queries)
                   ▼
       ┌────────────────────────┐
       │   cli_app Container    │
       └────────────────────────┘
```

### Ingestion Details
1.  **Extract (Ingestion Layer)**: The `extractor` container queries the API Ninjas Cars API `/v1/cars` endpoint by cycling through target makes and production years. Authentication is stateless, injecting the API Key into the request headers via `X-Api-Key`.
    > [!IMPORTANT]
    > **Free Tier Support**: API Ninjas restricts the `limit` query parameter to premium users only. The extraction client omits `limit` by default to remain fully compatible with standard Free API Keys.
2.  **Bronze Layer (`source_db`)**: The raw JSON arrays returned by the API are inserted into `raw_requests` exactly as received, leveraging PostgreSQL's `JSONB` data type. A `processed` boolean index flag manages incremental loading.
3.  **Transform (Processing Layer)**: The `transformer` container queries the Bronze layer for unprocessed records (`processed = FALSE`), flattens the JSON layout, cleans values (e.g. mapping drivetrain abbreviations `fwd` -> `FWD`, standardizing transmission abbreviations), validates datatypes, and extracts lookup keys.
4.  **Silver Layer (`target_db`)**: Data is normalized into 3NF-ish structures: dimension lookup tables (`makes`, `vehicle_classes`) and the central fact table (`car_models`). A composite unique constraint ensures strict deduplication.
5.  **Load (Presentation Layer)**: The `cli_app` container provides an interactive menu loop querying statistics and search results directly from the Silver layer under a secure, read-only session.

---

## 2. Repository Structure

```text
car-data-pipeline/
├── docker-compose.yml        # Multi-container orchestration configurations
├── .env                      # Local environment configurations (credentials, keys)
├── .gitignore                # Excludes virtual envs, secrets, and caches from git
├── requirements.txt          # Shared Python dependencies
├── README.md                 # Project user guide and technical specifications
│
├── sql/
│   ├── 01_target_schema.sql  # Database schema definitions for target_db (Silver)
│   ├── 02_indexes.sql        # Database performance tuning indexes script (Silver)
│   └── source_schema.sql     # Database schema definitions for source_db (Bronze)
│
├── extractor/
│   ├── Dockerfile            # Container configuration for Ingestion layer
│   ├── main.py               # Main pipeline orchestration loops
│   ├── api.py                # API Ninjas HTTP REST client wrapper
│   ├── auth.py               # Stateless API key authentication handler
│   ├── database.py           # Bronze DB transaction insert wrapper
│   ├── logger.py             # Standardized structured stdout formatting
│   ├── config.py             # Config loader with environment validations
│   └── utils.py              # Exponential backoff retry decorators with jitter
│
├── transformer/
│   ├── Dockerfile            # Container configuration for Processing layer
│   ├── main.py               # Main transformation loop orchestrator
│   ├── database.py           # Transaction load managers for Bronze & Silver DBs
│   ├── transform.py          # Data flattening and normalization logic
│   ├── validation.py         # Business logic boundary quality validations
│   ├── logger.py             # Standardized structured logs configuration
│   └── config.py             # Config validator for ETL connection details
│
├── cli_app/
│   ├── Dockerfile            # Container configuration for Interactive presentation layer
│   ├── main.py               # Presentation bootstrap runner
│   ├── menu.py               # Navigation menu loops & tabular output rendering
│   ├── queries.py            # pre-compiled SELECT statistics query structures
│   ├── database.py           # Target DB read-only connection wrappers
│   └── config.py             # CLI database configurations loader
│
└── tests/
    ├── test_extractor.py     # Unit test suite verifying extractor & retry decorator
    └── test_transformer.py   # Unit test suite verifying transform mapping & bounds
```

---

## 3. Configuration & Setup

### Prerequisites
*   [Docker](https://docs.docker.com/get-docker/) installed.
*   [Docker Compose](https://docs.docker.com/compose/install/) installed.
*   An active [API Ninjas Key](https://api-ninjas.com/) (Free tier provides 60 RPM).

### Environment Configuration
1.  Create a `.env` file in the root directory:
    ```ini
    # API Ninjas Cars API Configuration
    API_NINJAS_API_KEY=your_api_key_here

    # Source Database Configuration (Bronze Layer)
    SOURCE_DB_HOST=source_db
    SOURCE_DB_PORT=5432
    SOURCE_DB_USER=raw_user
    SOURCE_DB_PASSWORD=raw_secure_password_123
    SOURCE_DB_NAME=raw_db

    # Target Database Configuration (Silver Layer)
    TARGET_DB_HOST=target_db
    TARGET_DB_PORT=5432
    TARGET_DB_USER=analytics_user
    TARGET_DB_PASSWORD=analytics_secure_password_123
    TARGET_DB_NAME=analytics_db
    ```
2.  Replace `your_api_key_here` with your actual API Ninjas key.
3.  If host port conflicts exist on your machine (e.g. local PostgreSQL runs on port `5432`), the docker-compose configuration shifts:
    *   `source_db` host port is exposed on `5431`
    *   `target_db` host port is exposed on `5433`
    *   *No internal port changes are required since containers talk on bridge network port `5432`.*

---

## 4. Run Instructions

### 1. Build and Start the Database Engines
Spin up the PostgreSQL database containers. They will automatically run the SQL initialization schemas and indexes in the correct order:
```bash
docker compose up -d source_db target_db
```

### 2. Execute Data Extraction (Ingest to Bronze)
Trigger the `extractor` container to fetch data. It iterates over targeted makes and years, storing raw outputs inside the Bronze database:
```bash
docker compose build extractor
docker compose run --rm extractor
```

### 3. Execute Transformation (Ingest to Silver)
Trigger the `transformer` container to parse, clean, validate, and load data into Silver tables:
```bash
docker compose build transformer
docker compose run --rm transformer
```

### 4. Run the Interactive Analytics CLI
Start the presentation layer to query data. Stdin and TTY are attached for terminal interaction:
```bash
docker compose build cli_app
docker compose run --rm cli_app
```

---

## 5. Testing

Unit tests run using Python's standard `unittest` library and mock libraries, completing in milliseconds by patching sleep backoffs:

Run the test suite from the root workspace directory:
```bash
PYTHONPATH=. python -m unittest discover -s tests
```

---

## 6. Design and Engineering Standards

*   **SOLID & DRY Principles**: Strict separation of concerns. Ingestion clients, authentication decorators, database connection pools, and CLI query files are decoupled.
*   **Stateless Authentication**: Header-based `X-Api-Key` validations avoid token refresh complexities.
*   **Fail-Safe Ingestion Retry**: Exponential backoff with random jitter handles network hiccups and rate limiting.
*   **Silver Database Integrity**: A composite unique constraint on `car_models` deduplicates incoming datasets.
*   **Secure CLI Read-Only Sessions**: Autocommit is enabled and sessions are restricted to `readonly=True`, preventing database writes or mutations from the CLI layer.
