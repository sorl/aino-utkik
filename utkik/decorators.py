from functools import wraps
from django.http import HttpResponse


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
    def outer(f):
        @wraps(f)
        def wrapper(request, *args, **kwargs):
            if not request.method in methods:
                return HttpResponse(status=405)
            return f(request, *args, **kwargs)
        return wrapper
    return outer


def remove_request(f):
    """Removes the request argument"""
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


def handler_decorators(*decorators):
    """Converts function decorators into a decorator for ``utkik.BaseView``
    handlers.
    """
    def outer(f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            def g(request, *args, **kwargs):
                return f(self, *args, **kwargs)
            for d in reversed(decorators):
                g = d(g)
            return g(self.request, *args, **kwargs)
        return wrapper
    return outer

