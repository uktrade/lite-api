from functools import wraps

from django.core.cache import cache

from common.enums import LiteEnum, autostr

DEFAULT_CACHE_TIMEOUT = 60 * 60


class Key(LiteEnum):
    """
    LITE cache keys
    """

    STATUS_LIST = autostr()
    GOV_USERS_LIST = autostr()
    COUNTRIES_LIST = autostr()
    CONTROL_LIST_ENTRIES_LIST = autostr()


def generate_cache_key(key: Key):
    """
    Customisable for generating cache key, if complex keys are required.
    """
    return key


def lite_cache(key: Key, timeout=DEFAULT_CACHE_TIMEOUT):
    """
    Cache decorator
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_key = generate_cache_key(key)
            cached_value = cache.get(cache_key)
            if cached_value:
                # cache hit
                return cached_value
            value = f(*args, **kwargs)
            cache.set(cache_key, value, timeout)
            return value

        return wrapper

    return decorator


def lite_invalidate_cache(key):
    """Invalidate cache entry"""
    cache.delete(key)
