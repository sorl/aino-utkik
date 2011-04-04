from django.http import HttpResponse
from functools import wraps


def requires_ajax(f):
    """Enforces that the request is an ajax call"""
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponse(status=403)
        return f(request, *args, **kwargs)
    return wrapper


def http_methods(*methods):
    """Enforces one of the supplied HTTP methods"""
    def decorator(f):
        @wraps(f)
        def wrapper(request, *args, **kwargs):
            if not request.method in methods:
                return HttpResponse(status=405)
            return f(request, *args, **kwargs)
        return wrapper
    decorator.__name__ = 'http_methods'
    return decorator


def handler_decorator(*decorators):
    """Converts function decorators into a decorator for ``utkik.View``
    handlers.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            def g(request, *args, **kwargs):
                return f(self, *args, **kwargs)
            for d in reversed(decorators):
                g = d(g)
            return g(self.request, *args, **kwargs)
        return wrapper
    decorator.__name__ = 'handler_decorator'
    return decorator

