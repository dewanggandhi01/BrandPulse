from __future__ import annotations
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time

class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self._clients = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        if client_ip not in self._clients:
            self._clients[client_ip] = []
        
        # Cleanup old requests
        self._clients[client_ip] = [t for t in self._clients[client_ip] if now - t < self.window]
        
        if len(self._clients[client_ip]) >= self.max_requests:
            return Response(content="Rate limit exceeded", status_code=429)
        
        self._clients[client_ip].append(now)
        return await call_next(request)
