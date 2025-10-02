import json
from typing import Any, Optional
from django.core.cache import cache


def cache_set_json(key: str, value: Any, timeout: int = 600) -> None:
    cache.set(key, json.dumps(value, default=str), timeout=timeout)


def cache_get_json(key: str) -> Optional[Any]:
    data = cache.get(key)
    if not data:
        return None
    try:
        return json.loads(data)
    except Exception:
        return None
