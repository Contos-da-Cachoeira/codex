from contextvars import ContextVar
from functools import wraps


_current = ContextVar('wiki_catalog_request', default=None)


def request_cached(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        cache = _current.get()
        if cache is None:
            return function(*args, **kwargs)
        key = (function.__name__, args, tuple(sorted(kwargs.items())))
        if key not in cache:
            cache[key] = function(*args, **kwargs)
        return cache[key]
    return wrapped


def invalidate_catalog():
    cache = _current.get()
    if cache is not None:
        cache.clear()


class CatalogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _current.set({})
        try:
            return self.get_response(request)
        finally:
            _current.reset(token)
