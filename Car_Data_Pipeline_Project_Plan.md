# Car Data Pipeline

## Goal

Build a complete end-to-end ETL Data Pipeline that extracts vehicle data
from an external REST API, stores the raw responses, transforms them
into a relational model, loads them into a target PostgreSQL database,
and exposes an interactive CLI application for querying and analyzing
the data.

------------------------------------------------------------------------

# High-Level Architecture

``` text
                    Car API
                       │
                 HTTPS Requests
                       │
                       ▼
                Extractor Service
                       │
          Validate & Log Response
                       │
                       ▼
             Source PostgreSQL
            (Raw / Bronze Layer)
                       │
             Read JSONB Records
                       │
                       ▼
             Transformer Service
                       │
      Clean + Normalize + Validate
                       │
                       ▼
            Target PostgreSQL
          (Silver Relational Layer)
                       │
             SQL Queries / Analytics
                       │
                       ▼
              Interactive CLI App
```

------------------------------------------------------------------------

# Docker Architecture

``` text
Docker Compose
│
├── source_db
├── target_db
├── extractor
├── transformer
└── cli_app
```

------------------------------------------------------------------------

# Containers

## source_db

Stores the raw API responses exactly as received.

-   No cleaning
-   No transformations
-   No business logic

Acts as the landing (Bronze) layer.

## target_db

Stores cleaned relational tables optimized for querying.

The CLI interacts only with this database.

## extractor

Responsibilities:

-   Authenticate with the API
-   Request data
-   Retry failed requests
-   Validate responses
-   Store raw JSON
-   Log extraction status

Never performs transformations.

## transformer

Responsibilities:

-   Read raw JSON from source_db
-   Parse JSON
-   Clean data
-   Normalize values
-   Remove duplicates
-   Convert data types
-   Load into target_db

Never communicates directly with the API.

## cli_app

Provides an interactive terminal application.

Example:

``` text
1. Search by Make
2. Search by Year
3. List Models
4. Statistics
5. Exit
```

------------------------------------------------------------------------

# Folder Structure

``` text
car-data-pipeline/

├── docker-compose.yml
├── .env
├── .gitignore
├── README.md
├── requirements.txt
│
├── extractor/
│   ├── Dockerfile
│   ├── main.py
│   ├── api.py
│   ├── auth.py
│   ├── database.py
│   ├── logger.py
│   ├── config.py
│   └── utils.py
│
├── transformer/
│   ├── Dockerfile
│   ├── main.py
│   ├── database.py
│   ├── transform.py
│   ├── validation.py
│   ├── logger.py
│   ├── config.py
│   └── utils.py
│
├── cli_app/
│   ├── Dockerfile
│   ├── main.py
│   ├── menu.py
│   ├── queries.py
│   ├── database.py
│   └── config.py
│
├── sql/
│   ├── source_schema.sql
│   ├── target_schema.sql
│   └── indexes.sql
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── database.md
│
└── tests/
    ├── extractor/
    ├── transformer/
    └── cli/
```

------------------------------------------------------------------------

# Module Responsibilities

## extractor

### api.py

Contains all HTTP requests.

-   login()
-   fetch_models()
-   fetch_makes()
-   fetch_years()
-   fetch_trims()

Only this module imports `requests`.

### auth.py

Authentication logic only.

Returns JWT token.

### database.py

Database operations only.

-   connect()
-   create_tables()
-   insert_raw()
-   fetch_raw()

### config.py

Loads environment variables from `.env`.

### logger.py

Logs extraction lifecycle.

### utils.py

Shared helper utilities.

### main.py

Workflow:

``` text
Authenticate
    ↓
Fetch API
    ↓
Validate
    ↓
Save Raw
```

------------------------------------------------------------------------

## transformer

### transform.py

Business logic only.

-   Rename columns
-   Remove duplicates
-   Drop nulls
-   Normalize values
-   Convert types
-   Flatten nested JSON

### validation.py

Quality checks.

### database.py

Reads from source_db and writes to target_db.

### main.py

Workflow

``` text
Read Raw
   ↓
Transform
   ↓
Validate
   ↓
Insert Clean
```

------------------------------------------------------------------------

## cli_app

### menu.py

Interactive menu.

### queries.py

SQL queries only.

### database.py

Database connection.

------------------------------------------------------------------------

# SQL

Keep SQL outside Python.

-   source_schema.sql
-   target_schema.sql
-   indexes.sql

------------------------------------------------------------------------

# Source Database

Database:

`raw_db`

Table:

`raw_requests`

Columns

-   request_id
-   endpoint
-   request_parameters
-   retrieved_at
-   status_code
-   payload (JSONB)

Raw responses are never modified.

------------------------------------------------------------------------

# Target Database

Database:

`analytics_db`

Main table:

`car_models`

Suggested columns

-   model_id
-   make
-   model
-   year
-   trim
-   engine
-   fuel_type
-   body_type
-   drive_type
-   transmission
-   created_at

------------------------------------------------------------------------

# Data Flow

``` text
API
 ↓
Extractor
 ↓
Source PostgreSQL (JSONB)
 ↓
Transformer
 ↓
Target PostgreSQL
 ↓
CLI
```

------------------------------------------------------------------------

# Environment Variables

-   API_TOKEN
-   API_SECRET
-   SOURCE_DB_HOST
-   SOURCE_DB_PORT
-   SOURCE_DB_USER
-   SOURCE_DB_PASSWORD
-   TARGET_DB_HOST
-   TARGET_DB_PORT
-   TARGET_DB_USER
-   TARGET_DB_PASSWORD

------------------------------------------------------------------------

# Logging

Every service should produce timestamped INFO/WARNING/ERROR logs.

------------------------------------------------------------------------

# Future Improvements

-   Airflow
-   Incremental loading
-   Scheduling
-   Unit tests
-   Data quality checks
-   Alembic
-   SQLAlchemy
-   FastAPI
-   Grafana
-   Prometheus
-   GitHub Actions
-   AWS Deployment (ECR + EC2)

------------------------------------------------------------------------

# Design Principles

1.  One responsibility per container.
2.  One responsibility per module.
3.  API logic and database logic are separated.
4.  Transformations are isolated from extraction.
5.  Preserve all raw data.
6.  Target DB contains only clean, validated data.
7.  Configuration comes from environment variables.
8.  SQL schemas are version-controlled.
9.  CLI reads only from target_db.
10. Docker Compose orchestrates services only.
