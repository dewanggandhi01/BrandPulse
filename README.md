# BrandPulse 🚀

**Brand Intelligence & Autonomous Competitor Tracking Platform**

BrandPulse is an enterprise-grade platform that continuously monitors target brands and rivals across eight core intelligence vectors: web crawling, algorithmic SEO auditing, product & pricing parity, website change diffing, competitor benchmarking, social sentiment & reputation, paid advertising velocity, and executive brief synthesis.

---

## 🏛️ System Architecture

BrandPulse is engineered as a high-performance monorepo leveraging FastAPI, React 19, Celery, Redis, and PostgreSQL 17.

```mermaid
graph TD
    Client[React 19 SPA + Vite + Tailwind v4] -->|REST API / JSON| API[FastAPI Backend Application]
    API -->|Async Engine| DB[(PostgreSQL 17)]
    API -->|Async Cache / Lock| Redis[(Redis 7.4)]
    
    API -->|Enqueues Jobs| Redis
    Redis -->|Queue: scraping| ScraperWorker[Celery Solo Worker: Crawling & Ads]
    Redis -->|Queue: analysis,seo,diffing| ComputeWorker[Celery Prefork Worker: SEO, NLP, Diffs, Reports]
    
    ScraperWorker -->|HTTP / Playwright| TargetWeb[Monitored Brand Domains]
    ScraperWorker -->|Snapshots & Hashes| DB
    ComputeWorker -->|Audits & Intelligence| DB
```

---

## ⚡ Core Feature Matrix

| Pillar | Engine Module | Key Capabilities |
|---|---|---|
| **1. Crawling Engine** | `workers/scrapers/` | 3-tier scraping (HTTP, API, Playwright), RFC 9309 robots parser with TTL caching, token bucket rate limiter, SHA-256 deduplication. |
| **2. SEO Audit Engine** | `workers/seo/` | 4-pillar algorithmic scoring (Technical 30%, Content 35%, Schema 15%, Links 20%) evaluating 43+ checks with remediation tips. |
| **3. Product & Pricing** | `workers/extraction/` | Multi-strategy extraction (JSON-LD $\to$ Hydration state $\to$ CSS DOM), currency normalization, >50% anomaly detection, time-series history. |
| **4. Website Changes** | `workers/diffing/` | DOM cleaner, SequenceMatcher comparator, algorithmic classifier (`pricing_change`, `messaging_pivot`, `layout_overhaul`, `seo_change`). |
| **5. Competitor Intelligence**| `backend/app/api/v1/competitors.py` | Rival linking, multi-brand benchmark radar charts, relative price indexing. |
| **6. Social Sentiment** | `workers/sentiment/` | VADER-style multi-lexicon sentiment analysis, negation handling, Net Sentiment Score (NSS: -100 to +100), topic extraction. |
| **7. Paid Ad Intelligence** | `workers/ads/` | Creative headline/copy/CTA extraction, platform breakdown, longevity estimator ($\le 3$d Pilot, $4-14$d Active, $15-45$d Scaling, $>45$d Evergreen). |
| **8. Executive Reports** | `workers/reports/` | Multi-source aggregator, composite health score (0-100), 4-quadrant SWOT matrix, printable C-suite briefs. |

---

## 🚀 Quick Start with Docker Compose

1. Clone the repository:
   ```bash
   git clone <repo_url>
   cd brandpulse
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

3. Start all 8 services:
   ```bash
   docker-compose up -d --build
   ```

4. Access the platforms:
   - **Frontend Dashboard**: `http://localhost:5173`
   - **FastAPI OpenAPI Documentation**: `http://localhost:8000/docs`
   - **Celery Flower (if enabled)**: `http://localhost:5555`

---

## ⚙️ Environment Configuration

| Variable | Description | Default (Docker) | Default (Local Dev) |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://brandpulse:brandpulse@postgres:5432/brandpulse` | `postgresql+asyncpg://brandpulse:brandpulse@localhost:5432/brandpulse` |
| `POSTGRES_USER` | PostgreSQL superuser | `brandpulse` | `brandpulse` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `brandpulse` | `brandpulse` |
| `POSTGRES_DB` | PostgreSQL database name | `brandpulse` | `brandpulse` |
| `REDIS_URL` | Redis cache & app connection URL | `redis://redis:6379/0` | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery task message broker | `redis://redis:6379/1` | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery task result backend | `redis://redis:6379/2` | `redis://localhost:6379/2` |
| `API_V1_PREFIX` | FastAPI route prefix | `/api/v1` | `/api/v1` |
| `CORS_ORIGINS` | Explicit allowed HTTP origins | `["http://localhost:5173","http://localhost:3000"]` | `["http://localhost:5173","http://localhost:3000"]` |
| `LOG_LEVEL` | structlog logging level | `INFO` | `INFO` |

---

## 💻 Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 17
- Redis 7.4

### 1. Backend & Workers
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r backend/requirements.txt
pip install -r workers/requirements.txt

# Run FastAPI dev server
uvicorn backend.app.main:app --reload --port 8000

# Run Celery workers
celery -A workers.celery_app worker -Q scraping --pool=solo --loglevel=info
celery -A workers.celery_app worker -Q analysis,seo,diffing --concurrency=4 --loglevel=info
```

### 2. Frontend Application
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing & Verification

Run the full automated test suite:

```bash
# Run all backend & worker unit and API tests (45 tests)
python -m pytest workers/tests backend/tests -v

# Run frontend production build & type check
cd frontend && npm run build
```

---

## 📚 Diátaxis Documentation Suite

- 📖 **API Reference**: [docs/api_reference.md](docs/api_reference.md) — Exhaustive REST endpoints specification
- 🛠️ **Operations Runbook**: [docs/runbooks/operations.md](docs/runbooks/operations.md) — Production deployment, Celery scaling, and backups
- 🔍 **Troubleshooting Guide**: [docs/troubleshooting.md](docs/troubleshooting.md) — Symptom → Cause → Resolution matrix
- 🏛️ **Architecture & C4 Diagrams**: [docs/architecture.md](docs/architecture.md) — Container and context designs
- 📝 **Architecture Decision Records**: [docs/adr/001-monorepo-structure.md](docs/adr/001-monorepo-structure.md) — Monorepo structural decisions

---

## 📄 License
This project is licensed under the MIT License.
