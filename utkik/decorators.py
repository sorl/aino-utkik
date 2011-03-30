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


def allowed_methods(methods):
    """Enforces a list of supplied HTTP methods"""
    def outer(f):
        @wraps(f)
        def wrapper(request, *args, **kwargs):
            if not request.method in methods:
                return HttpResponse(status=405)
            return f(request, *args, **kwargs)
        return wrapper
    return outer


def decorate(decorators):
    """A decorator that applies a list of decorators in reverse order"""
    def decorator(f):
        for d in reversed(decorators):
            f = d(f)
        return f
    return decorator

