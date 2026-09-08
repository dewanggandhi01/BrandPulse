# BrandPulse Architecture

This document describes the high-level architecture of BrandPulse using the C4 model.

## System Context Diagram

```mermaid
C4Context
    title System Context for BrandPulse

    Person(customer, "Customer", "A user of the BrandPulse platform.")
    System(brandpulse, "BrandPulse", "Allows customers to track brand intelligence and competitors.")
    System_Ext(competitor_sites, "Competitor Websites", "Public websites scraped for intelligence.")
    System_Ext(llm_provider, "LLM Provider", "External service for text analysis (e.g., OpenAI).")

    Rel(customer, brandpulse, "Uses")
    Rel(brandpulse, competitor_sites, "Scrapes data from")
    Rel(brandpulse, llm_provider, "Sends text for analysis to")
```

## Container Diagram

```mermaid
C4Container
    title Container Diagram for BrandPulse

    Person(customer, "Customer", "A user of the BrandPulse platform.")

    System_Boundary(c1, "BrandPulse") {
        Container(frontend, "Frontend App", "React, TypeScript", "Provides the user interface.")
        Container(backend, "API Application", "FastAPI, Python", "Provides API endpoints and business logic.")
        ContainerDb(db, "Database", "PostgreSQL", "Stores user data, brand intelligence, and system state.")
        ContainerDb(cache, "Cache & Message Broker", "Redis", "Caches data and queues background jobs.")
        Container(worker_scraping, "Scraping Worker", "Celery, Playwright", "Handles web scraping tasks.")
        Container(worker_analysis, "Analysis Worker", "Celery", "Handles data analysis and SEO diffing tasks.")
        Container(worker_beat, "Beat Scheduler", "Celery Beat", "Schedules periodic tasks.")
    }

    System_Ext(competitor_sites, "Competitor Websites", "Public websites scraped for intelligence.")

    Rel(customer, frontend, "Visits", "HTTPS")
    Rel(frontend, backend, "Makes API calls to", "JSON/HTTPS")
    Rel(backend, db, "Reads from and writes to", "SQL/TCP")
    Rel(backend, cache, "Reads from and writes to", "Redis Protocol")
    Rel(worker_scraping, cache, "Pulls jobs from", "Redis Protocol")
    Rel(worker_analysis, cache, "Pulls jobs from", "Redis Protocol")
    Rel(worker_beat, cache, "Pushes jobs to", "Redis Protocol")
    Rel(worker_scraping, db, "Reads from and writes to", "SQL/TCP")
    Rel(worker_analysis, db, "Reads from and writes to", "SQL/TCP")
    
    Rel(worker_scraping, competitor_sites, "Scrapes", "HTTPS")
```

## Container Responsibilities

- **Frontend App:** The user interface built with React. It communicates with the backend API.
- **API Application (Backend):** The core FastAPI service serving REST endpoints, managing authentication, and handling synchronous business logic.
- **Database (PostgreSQL):** The primary persistent storage for the platform.
- **Cache & Message Broker (Redis):** Used for fast data caching and as the message broker for Celery queues.
- **Scraping Worker:** A Celery worker configured specifically for IO-bound web scraping tasks using Playwright.
- **Analysis Worker:** A Celery worker configured for CPU-bound or external API-bound tasks like data analysis, NLP, and SEO diffing.
- **Beat Scheduler:** Celery Beat service responsible for dispatching periodic background tasks (e.g., daily scraping).
