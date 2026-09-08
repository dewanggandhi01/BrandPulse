from __future__ import annotations
import structlog
import logging
from app.middleware.request_id import request_id_ctx_var

def get_request_id(_, __, event_dict):
    req_id = request_id_ctx_var.get()
    if req_id:
        event_dict["request_id"] = req_id
    return event_dict

def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            get_request_id,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=logging.INFO, format="%(message)s")
