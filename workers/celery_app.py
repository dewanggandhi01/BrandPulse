from __future__ import annotations
try:
    from celery import Celery
except ImportError:
    class Celery:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            self.conf = {}
        def task(self, *args, **kwargs):
            def decorator(fn):
                fn.apply_async = lambda *a, **k: None
                fn.delay = lambda *a, **k: None
                fn.retry = lambda *a, **k: None
                return fn
            return decorator
        def autodiscover_tasks(self, *args, **kwargs):
            pass

import os

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

app = Celery("brandpulse_workers", broker=broker_url, backend=result_backend)
if hasattr(app, "conf") and hasattr(app.conf, "update"):
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_routes={
            "workers.tasks.scraping.*": {"queue": "scraping"},
            "workers.tasks.extraction.*": {"queue": "scraping"},
            "workers.tasks.analysis.*": {"queue": "analysis"},
            "workers.tasks.seo.*": {"queue": "seo"},
            "workers.tasks.diffing.*": {"queue": "diffing"},
        },
    )

app.autodiscover_tasks([
    "workers.tasks.scraping",
    "workers.tasks.extraction",
    "workers.tasks.analysis",
    "workers.tasks.seo",
    "workers.tasks.diffing",
    "workers.tasks.monitoring"
])
