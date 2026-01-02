# Cold Start Analyzer

A serverless cold start analysis tool that helps developers understand why their Lambda functions have slow cold starts and how to fix them.

## Project Overview

### Problem
Serverless developers see "Init Duration: 2,800ms" in CloudWatch but have no idea WHY. They don't know which dependencies are slow or how to optimize.

### Solution
A lightweight SDK that captures module load times during Lambda cold starts and sends data to a backend. Grafana dashboards visualize the breakdown and show optimization recommendations.

### How It Works
```
Lambda Function (with SDK)
    │
    │ POST /api/v1/ingest
    │ { moduleTimings, coldStart, ... }
    ▼
FastAPI Backend
    │
    │ Store
    ▼
PostgreSQL Database
    │
    │ Query
    ▼
Grafana Dashboards
```

## Architecture

### Components

1. **SDK (TypeScript)** - npm package installed in customer's Lambda
2. **Backend (FastAPI)** - Receives and stores telemetry data
3. **Database (PostgreSQL)** - Stores invocation data
4. **Grafana** - Visualizes data with pre-built dashboards

### Data Flow

1. Customer installs SDK in their Lambda
2. SDK hooks into require/import to capture module load times
3. At function end, SDK sends data to backend API
4. Backend validates and stores in PostgreSQL
5. Grafana queries PostgreSQL and displays dashboards

## Tech Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Testing**: pytest, pytest-asyncio

### SDK
- **Language**: TypeScript
- **Target**: Node.js 18+
- **Build**: tsup
- **Package Manager**: npm
- **Testing**: vitest

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **Reverse Proxy**: Nginx (production)
- **Grafana**: v10+

## Project Structure
```
coldstart-analyzer/
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── alembic.ini
│   ├── pyproject.toml
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── config.py               # Settings and configuration
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # Main API router
│   │   │   ├── deps.py             # Dependencies (db session, auth)
│   │   │   │
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── ingest.py       # POST /api/v1/ingest
│   │   │       ├── functions.py    # GET /api/v1/functions
│   │   │       ├── health.py       # GET /api/v1/health
│   │   │       └── api_keys.py     # API key management
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # SQLAlchemy base
│   │   │   ├── invocation.py       # Invocation model
│   │   │   ├── function.py         # Function model
│   │   │   ├── project.py          # Project model
│   │   │   └── api_key.py          # API key model
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py           # Ingest request/response schemas
│   │   │   ├── function.py         # Function schemas
│   │   │   └── common.py           # Common schemas
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ingest_service.py   # Ingest business logic
│   │   │   └── analysis_service.py # Analysis/recommendations
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py          # Database session
│   │   │   └── init_db.py          # Database initialization
│   │   │
│   │   └── core/
│   │       ├── __init__.py
│   │       ├── security.py         # API key validation
│   │       └── exceptions.py       # Custom exceptions
│   │
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_ingest.py
│       └── test_health.py
│
├── sdk/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsup.config.ts
│   ├── README.md
│   │
│   ├── src/
│   │   ├── index.ts                # Main export
│   │   ├── wrapper.ts              # Lambda handler wrapper
│   │   ├── collector.ts            # Data collection logic
│   │   ├── sender.ts               # HTTP sender
│   │   ├── hooks/
│   │   │   ├── require-hook.ts     # CommonJS require hook
│   │   │   └── module-timing.ts    # Module timing capture
│   │   ├── types.ts                # TypeScript types
│   │   └── utils.ts                # Utility functions
│   │
│   └── tests/
│       ├── wrapper.test.ts
│       └── collector.test.ts
│
├── grafana/
│   ├── provisioning/
│   │   ├── dashboards/
│   │   │   ├── dashboard.yml       # Dashboard provisioning config
│   │   │   └── cold-start-analyzer.json  # Main dashboard
│   │   │
│   │   └── datasources/
│   │       └── datasource.yml      # PostgreSQL datasource config
│   │
│   └── grafana.ini                 # Grafana configuration
│
└── docs/
    ├── setup.md
    ├── sdk-usage.md
    └── api-reference.md
```

## Database Schema

### Tables

#### projects
Represents a customer project/account.
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### api_keys
API keys for authentication.
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,  -- SHA256 hash of the actual key
    key_prefix VARCHAR(10) NOT NULL, -- First 8 chars for identification
    name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_project_id ON api_keys(project_id);
```

#### functions
Represents a Lambda function being tracked.
```sql
CREATE TABLE functions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    function_name VARCHAR(255) NOT NULL,
    runtime VARCHAR(50),
    region VARCHAR(50),
    memory_allocated_mb INTEGER,
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(project_id, function_name)
);

CREATE INDEX idx_functions_project_id ON functions(project_id);
```

#### invocations
Stores each Lambda invocation's data.
```sql
CREATE TABLE invocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    function_id UUID NOT NULL REFERENCES functions(id) ON DELETE CASCADE,
    
    -- Invocation identifiers
    invocation_id VARCHAR(255),
    request_id VARCHAR(255),
    
    -- Timing data
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    cold_start BOOLEAN NOT NULL,
    init_duration_ms INTEGER,           -- Cold start init time
    execution_duration_ms INTEGER NOT NULL,
    billed_duration_ms INTEGER,
    
    -- Memory data
    memory_used_mb INTEGER,
    memory_allocated_mb INTEGER,
    
    -- Module timings (stored as JSONB)
    module_timings JSONB,               -- {"aws-sdk": 850, "prisma": 620, ...}
    
    -- Additional context
    runtime_version VARCHAR(50),
    architecture VARCHAR(20),           -- x86_64 or arm64
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_invocations_function_id ON invocations(function_id);
CREATE INDEX idx_invocations_timestamp ON invocations(timestamp);
CREATE INDEX idx_invocations_cold_start ON invocations(cold_start);
CREATE INDEX idx_invocations_function_timestamp ON invocations(function_id, timestamp DESC);

-- Partitioning by month for large scale (optional, implement later)
-- CREATE TABLE invocations_y2026m01 PARTITION OF invocations
--     FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

## API Endpoints

### Authentication
All endpoints except `/health` require an API key in the header:
```
X-API-Key: csa_xxxxxxxxxxxxxxxxxxxx
```

### Endpoints

#### Health Check
```
GET /api/v1/health

Response 200:
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-01-02T10:30:00Z"
}
```

#### Ingest Telemetry Data
```
POST /api/v1/ingest

Headers:
    X-API-Key: csa_xxxxxxxxxxxxxxxxxxxx
    Content-Type: application/json

Request Body:
{
    "function_name": "payment-service",
    "invocation_id": "abc-123-def",
    "request_id": "req-456",
    "timestamp": "2026-01-02T10:30:00Z",
    "cold_start": true,
    "init_duration_ms": 2850,
    "execution_duration_ms": 145,
    "billed_duration_ms": 3000,
    "memory_used_mb": 180,
    "memory_allocated_mb": 512,
    "module_timings": {
        "aws-sdk": 850,
        "@prisma/client": 680,
        "moment": 340,
        "lodash": 180,
        "axios": 95,
        "./src/handlers/payment": 45
    },
    "runtime_version": "nodejs18.x",
    "architecture": "x86_64"
}

Response 200:
{
    "status": "ok",
    "invocation_id": "abc-123-def"
}

Response 400:
{
    "detail": "Validation error",
    "errors": [...]
}

Response 401:
{
    "detail": "Invalid or missing API key"
}
```

#### Batch Ingest (for efficiency)
```
POST /api/v1/ingest/batch

Headers:
    X-API-Key: csa_xxxxxxxxxxxxxxxxxxxx
    Content-Type: application/json

Request Body:
{
    "invocations": [
        { ... },  // Same schema as single ingest
        { ... },
        { ... }
    ]
}

Response 200:
{
    "status": "ok",
    "processed": 3,
    "failed": 0
}
```

#### List Functions
```
GET /api/v1/functions

Headers:
    X-API-Key: csa_xxxxxxxxxxxxxxxxxxxx

Response 200:
{
    "functions": [
        {
            "id": "uuid",
            "function_name": "payment-service",
            "runtime": "nodejs18.x",
            "region": "us-east-1",
            "memory_allocated_mb": 512,
            "last_seen_at": "2026-01-02T10:30:00Z",
            "cold_start_stats": {
                "avg_init_duration_ms": 2850,
                "cold_start_rate": 0.12,
                "total_invocations_24h": 15000
            }
        }
    ]
}
```

#### Get Function Details
```
GET /api/v1/functions/{function_id}

Headers:
    X-API-Key: csa_xxxxxxxxxxxxxxxxxxxx

Response 200:
{
    "id": "uuid",
    "function_name": "payment-service",
    "runtime": "nodejs18.x",
    "memory_allocated_mb": 512,
    "module_breakdown": {
        "aws-sdk": {
            "avg_load_time_ms": 850,
            "p50_ms": 820,
            "p95_ms": 920,
            "p99_ms": 1050
        },
        "@prisma/client": {
            "avg_load_time_ms": 680,
            "p50_ms": 650,
            "p95_ms": 780,
            "p99_ms": 850
        }
    },
    "recommendations": [
        {
            "module": "aws-sdk",
            "issue": "Loading entire SDK at startup",
            "suggestion": "Use modular @aws-sdk/client-* packages",
            "potential_savings_ms": 750
        }
    ]
}
```

## SDK Design

### Installation
```bash
npm install @coldstart/analyzer
```

### Basic Usage
```typescript
// CommonJS
const { analyze } = require('@coldstart/analyzer');

exports.handler = analyze(async (event, context) => {
    // Your Lambda code
    return { statusCode: 200, body: 'OK' };
});

// ESM
import { analyze } from '@coldstart/analyzer';

export const handler = analyze(async (event, context) => {
    // Your Lambda code
    return { statusCode: 200, body: 'OK' };
});
```

### Configuration
```typescript
const { analyze } = require('@coldstart/analyzer');

exports.handler = analyze(async (event, context) => {
    // Your code
}, {
    apiKey: process.env.COLDSTART_API_KEY,  // Required
    endpoint: 'https://api.coldstart.dev',  // Optional, defaults to production
    enabled: process.env.NODE_ENV === 'production',  // Optional, default true
    sampleRate: 1.0,  // Optional, 1.0 = 100% of invocations
    timeout: 1000,    // Optional, max ms to wait for sending data
});
```

### Environment Variables
SDK also reads from environment variables:
```
COLDSTART_API_KEY=csa_xxxxxxxxxxxxxxxxxxxx
COLDSTART_ENDPOINT=https://api.coldstart.dev
COLDSTART_ENABLED=true
COLDSTART_SAMPLE_RATE=1.0
```

### SDK Internals

#### Module Timing Capture
```typescript
// Hook into Node.js require
const Module = require('module');
const originalRequire = Module.prototype.require;
const moduleTimings: Record<string, number> = {};

Module.prototype.require = function(id: string) {
    const start = process.hrtime.bigint();
    const result = originalRequire.apply(this, arguments);
    const end = process.hrtime.bigint();
    
    const durationMs = Number(end - start) / 1e6;
    
    // Only track if > 1ms to reduce noise
    if (durationMs > 1) {
        moduleTimings[id] = (moduleTimings[id] || 0) + durationMs;
    }
    
    return result;
};
```

#### Cold Start Detection
```typescript
let isFirstInvocation = true;
let initEndTime: number;

// Capture when init phase ends (first handler call)
function detectColdStart(): boolean {
    if (isFirstInvocation) {
        initEndTime = Date.now();
        isFirstInvocation = false;
        return true;
    }
    return false;
}
```

#### Data Sending
```typescript
// Send data asynchronously at end of invocation
// Use non-blocking approach to not delay Lambda response

async function sendData(data: InvocationData): Promise<void> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1000);
    
    try {
        await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey,
            },
            body: JSON.stringify(data),
            signal: controller.signal,
        });
    } catch (e) {
        // Silently fail - don't impact customer's Lambda
        console.warn('[ColdStart] Failed to send telemetry:', e.message);
    } finally {
        clearTimeout(timeout);
    }
}
```

## Grafana Dashboard

### Datasource Configuration
```yaml
# grafana/provisioning/datasources/datasource.yml
apiVersion: 1

datasources:
  - name: ColdStart PostgreSQL
    type: postgres
    url: ${POSTGRES_HOST}:5432
    database: coldstart
    user: ${POSTGRES_USER}
    secureJsonData:
      password: ${POSTGRES_PASSWORD}
    jsonData:
      sslmode: disable
      maxOpenConns: 10
      maxIdleConns: 5
      connMaxLifetime: 14400
```

### Dashboard Panels

#### Panel 1: Cold Start Overview
```sql
-- Cold start rate over time
SELECT 
    time_bucket('1 hour', timestamp) AS time,
    COUNT(*) FILTER (WHERE cold_start = true) * 100.0 / COUNT(*) AS cold_start_rate
FROM invocations i
JOIN functions f ON i.function_id = f.id
WHERE f.project_id = '$project_id'
AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY time
ORDER BY time;
```

#### Panel 2: Average Init Duration by Function
```sql
SELECT 
    f.function_name,
    AVG(init_duration_ms) AS avg_init_duration,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY init_duration_ms) AS p95_init_duration
FROM invocations i
JOIN functions f ON i.function_id = f.id
WHERE f.project_id = '$project_id'
AND cold_start = true
AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY f.function_name
ORDER BY avg_init_duration DESC;
```

#### Panel 3: Module Timing Breakdown
```sql
SELECT 
    module_key AS module,
    AVG(module_value::numeric) AS avg_load_time_ms
FROM invocations i
JOIN functions f ON i.function_id = f.id,
    jsonb_each_text(module_timings) AS m(module_key, module_value)
WHERE f.function_name = '$function_name'
AND cold_start = true
AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY module_key
ORDER BY avg_load_time_ms DESC
LIMIT 20;
```

#### Panel 4: Cold Start vs Warm Execution Time
```sql
SELECT 
    CASE WHEN cold_start THEN 'Cold Start' ELSE 'Warm' END AS type,
    AVG(execution_duration_ms) AS avg_duration,
    COUNT(*) AS count
FROM invocations i
JOIN functions f ON i.function_id = f.id
WHERE f.project_id = '$project_id'
AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY cold_start;
```

## Configuration

### Environment Variables

#### Backend (.env)
```env
# Application
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/coldstart
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# CORS
CORS_ORIGINS=["http://localhost:3000","https://app.coldstart.dev"]

# Grafana
GRAFANA_URL=http://localhost:3000
```

#### SDK (Environment)
```env
COLDSTART_API_KEY=csa_xxxxxxxxxxxxxxxxxxxx
COLDSTART_ENDPOINT=https://api.coldstart.dev
COLDSTART_ENABLED=true
```

## Docker Compose

### Development
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/coldstart
      - APP_ENV=development
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend/app:/app/app  # Hot reload

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: coldstart
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  grafana:
    image: grafana/grafana:10.2.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - db

volumes:
  postgres_data:
  grafana_data:
```

## Dockerfiles

### Backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Requirements

### Backend (requirements.txt)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.26.0
```

### Backend Dev (requirements-dev.txt)
```
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0
black==24.1.0
ruff==0.1.14
mypy==1.8.0
```

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL 15+ (or use Docker)

### Quick Start
```bash
# Clone repository
git clone https://github.com/yourusername/coldstart-analyzer.git
cd coldstart-analyzer

# Start infrastructure
docker-compose up -d db grafana

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt -r requirements-dev.txt

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload

# SDK setup (in another terminal)
cd sdk
npm install
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# SDK tests
cd sdk
npm test
```

## API Key Format

API keys follow this format:
```
csa_[32 random alphanumeric characters]

Example: csa_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

- Prefix `csa_` identifies it as a ColdStart Analyzer key
- 32 character random string for security
- Only the hash is stored in database
- First 8 chars (prefix + 4) stored for identification: `csa_a1b2`

## Rate Limiting

### Ingest Endpoint
- 10,000 requests per minute per API key
- Batch endpoint counts as 1 request regardless of batch size

### Query Endpoints
- 100 requests per minute per API key

## Error Handling

### Standard Error Response
```json
{
    "detail": "Error message",
    "error_code": "VALIDATION_ERROR",
    "timestamp": "2026-01-02T10:30:00Z"
}
```

### Error Codes
- `VALIDATION_ERROR` - Invalid request data
- `AUTHENTICATION_ERROR` - Invalid or missing API key
- `RATE_LIMIT_ERROR` - Too many requests
- `NOT_FOUND` - Resource not found
- `INTERNAL_ERROR` - Server error

## Future Enhancements (Not in MVP)

1. **Recommendations Engine** - AI-powered suggestions based on module timings
2. **Alerts** - Notify when cold starts exceed threshold
3. **CI Integration** - Pre-deploy analysis
4. **Multi-runtime Support** - Python, Go, etc.
5. **Team Management** - Multiple users per project
6. **Billing** - Usage-based pricing with Stripe

## License

MIT

## Contributing

See CONTRIBUTING.md for guidelines.