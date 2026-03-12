"""
API Middleware for Logging and Metrics
======================================
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.logging_config import RequestLogger
from src.core.metrics import get_metrics


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.request_logger = RequestLogger()
        self.metrics = get_metrics()
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log."""
        start_time = time.time()
        
        # Process request
        response: Response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Extract user ID if available
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.id
        
        # Log request
        await self.request_logger.log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id
        )
        
        # Record metrics
        self.metrics.record_http_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        return response
