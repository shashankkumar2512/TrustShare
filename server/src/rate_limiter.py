from collections import defaultdict
from time import time
from fastapi import HTTPException, Request

# Simple in-memory rate limiter
_requests: dict = defaultdict(list)
MAX_REQUESTS = 100
WINDOW_SECONDS = 60

def rate_limit(request: Request):
    client = request.client.host if request.client else 'unknown'
    now = time()
    _requests[client] = [t for t in _requests[client] if now - t < WINDOW_SECONDS]
    if len(_requests[client]) >= MAX_REQUESTS:
        raise HTTPException(status_code=429, detail='Too many requests')
    _requests[client].append(now)
