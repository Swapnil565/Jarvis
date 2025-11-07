# app/utils/cache.py
import json
import hashlib
import asyncio
from functools import wraps
from typing import Callable, Any, Awaitable
from fastapi import Request
from starlette.responses import JSONResponse
from app.core.redis import get_redis
#hashlib is used for creating the unqiue keys
#Caching = Decorator wrapper + Key builder + Redis store/read 

def _hash_obj(obj: Any) -> str:
    #The api input can be big, so we hash them into keys that are short,string, and unqiue
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()

#build a cache key using, 
# function name

# path

# query

# request method

# extra data


async def _build_cache_key(
    func_name: str,
    request: Request | None,
    key_extra: dict | None,
) -> str:
    base = {"func": func_name}
    if request is not None:
        base.update({
            "path": request.url.path,
            "query": dict(request.query_params),
            "method": request.method,
        })
        

    if key_extra:
        base["extra"] = key_extra

    return f"cache:{_hash_obj(base)}"

# --- public API ------------------------------------------------------------

def cache_response(
    ttl: int = 60,
    vary_by_query: bool = True,
    vary_by_user: bool = False,  # set True if you cache user-specific data
    key_builder: Callable[[Request], dict] | None = None,  # add your own parts
):
    """
    Decorator for FastAPI endpoints that return JSON-serializable objects.
    - No need to touch Redis in routes.
    - Prevents thundering herd with a simple per-key lock.
    """
    def deco(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find Request object (FastAPI passes it if you declare it)
            request: Request | None = None
            for v in list(kwargs.values()) + list(args):
                if isinstance(v, Request):
                    request = v
                    break

            # Build key
            extra = key_builder(request) if (key_builder and request) else {}
            if not vary_by_query and request:
                extra["ignore_query"] = True
                request = Request(scope={**request.scope, "query_string": b""})

            if vary_by_user and request:
                uid = request.headers.get("x-user-id")
                if uid:
                    extra["uid"] = uid

            cache_key = await _build_cache_key(func.__name__, request, extra)
            lock_key = f"{cache_key}:lock"

            r = await get_redis()

            # Bypass cache if asked (useful for debugging)
            if request and request.headers.get("x-bypass-cache") == "1":
                data = await func(*args, **kwargs)
                return JSONResponse(content=data)

            # 1) Try cache
            cached = await r.get(cache_key)
            if cached:
                return JSONResponse(
                    content=json.loads(cached),
                    headers={"X-Cache": "HIT"},
                )

            # 2) Acquire a short lock to avoid stampede
            got_lock = await r.set(lock_key, "1", nx=True, ex=5)
            if not got_lock:
                # Someone else is computing; wait briefly for value
                for _ in range(10):
                    await asyncio.sleep(0.05)
                    cached = await r.get(cache_key)
                    if cached:
                        return JSONResponse(
                            content=json.loads(cached),
                            headers={"X-Cache": "HIT-WAIT"},
                        )
                # Timeout -> fall through and compute anyway

            # 3) Compute & store
            data = await func(*args, **kwargs)
            await r.setex(cache_key, ttl, json.dumps(data))
            await r.delete(lock_key)

            return JSONResponse(
                content=data,
                headers={
                    "X-Cache": "MISS",
                    "Cache-Control": f"public, max-age={ttl}",
                },
            )
        return wrapper
    return deco

# --- invalidation (call these on writes) -----------------------------------

async def cache_bust_by_prefix(prefix: str):
    """Dangerous on big sets; fine for scoped prefixes."""
    r = await get_redis()
    cursor = "0"
    while True:
        cursor, keys = await r.scan(cursor=cursor, match=f"{prefix}*",
                                    count=500)
        if keys:
            await r.delete(*keys)
        if cursor == "0":
            break

async def cache_bust_keys(keys: list[str]):
    r = await get_redis()
    if keys:
        await r.delete(*keys)


