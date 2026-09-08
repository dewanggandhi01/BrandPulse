from __future__ import annotations
from workers.celery_app import app
import structlog

logger = structlog.get_logger()

@app.task(name="workers.tasks.monitoring.placeholder_monitor")
def placeholder_monitor():
    logger.info("Monitoring placeholder")
    return {"status": "monitoring"}
