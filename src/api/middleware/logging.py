"""
Production-Grade Logging Middleware
Logs all API requests and responses with timing, status codes, and error tracking
"""

import time
import json
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses.
    
    Logs:
    - Request method, path, query params, headers (filtered)
    - Response status code, duration
    - Request/Response body (for non-file responses)
    - Errors with full stack traces
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = f"{int(time.time() * 1000)}"
        
        # Start timing
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        client_host = request.client.host if request.client else "unknown"
        
        # Log incoming request
        logger.info(
            f"[{request_id}] → {method} {path} "
            f"from {client_host} "
            f"{f'?{query_params}' if query_params else ''}"
        )
        
        # Log JSON body for POST/PUT/PATCH — only call request.body() (no _receive patching).
        # Starlette's BaseHTTPMiddleware caches the body on the request; replacing _receive
        # breaks _CachedRequest and causes: RuntimeError: Unexpected message received: http.request
        if method in ["POST", "PUT", "PATCH"]:
            try:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    body = await request.body()
                    if body:
                        try:
                            body_json = json.loads(body.decode())
                            masked_body = self._mask_sensitive_data(body_json)
                            logger.info(f"[{request_id}] Request Body: {json.dumps(masked_body)}")
                        except Exception:
                            logger.info(f"[{request_id}] Request Body: <non-json>")
            except Exception as e:
                logger.debug(f"[{request_id}] Could not read request body: {e}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            status_emoji = "✅" if response.status_code < 400 else "❌"
            logger.info(
                f"[{request_id}] ← {status_emoji} {response.status_code} "
                f"{method} {path} "
                f"in {duration_ms:.2f}ms"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            return response
            
        except Exception as exc:
            # Calculate duration even on error
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error with full details
            logger.error(
                f"[{request_id}] ❌ ERROR {method} {path} "
                f"after {duration_ms:.2f}ms: {str(exc)}",
                exc_info=True
            )
            
            # Re-raise to let global exception handler deal with it
            raise
    
    def _mask_sensitive_data(self, data: dict) -> dict:
        """Mask sensitive fields in logged data."""
        sensitive_keys = ['password', 'token', 'secret', 'api_key', 'apikey', 'authorization']
        
        if isinstance(data, dict):
            return {
                k: '***MASKED***' if any(s in k.lower() for s in sensitive_keys) else (
                    self._mask_sensitive_data(v) if isinstance(v, (dict, list)) else v
                )
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        
        return data
