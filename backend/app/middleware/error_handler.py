from __future__ import annotations
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
import traceback
import structlog

logger = structlog.get_logger()

def setup_error_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "detail": str(exc),
                "instance": str(request.url)
            },
            headers={"Content-Type": "application/problem+json"}
        )
