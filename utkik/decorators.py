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


def remove_request(f):
    """Removes the request argument"""
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        return f(*args, **kwargs)
    return wrapper

