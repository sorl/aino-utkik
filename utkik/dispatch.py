import re
from django.core.exceptions import ImproperlyConfigured
from django.core import urlresolvers
from django.utils.functional import update_wrapper, memoize
from django.utils.importlib import import_module


__all__ = ['handler404', 'handler500', 'include', 'patterns', 'url']


handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
_view_cache = {}
view_repr_pat = re.compile(r"\.(\w+)'>$")


def get_view(name):
    """
    Import and returns a view from sting
    """
    mod_name, attr = name.rsplit('.', 1)
    try:
        mod = import_module(mod_name)
        return getattr(mod, attr)
    except (ImportError, AttributeError), e:
        if not mod_name.endswith('.views'):
            try:
                mod = import_module(mod_name + '.views')
                return getattr(mod, attr)
            except Exception:
                pass
        raise e # original error
get_view = memoize(get_view, _view_cache, 1)


class LazyView(object):
    """
    Lazy wrapper for a view function or class
    """
    def __init__(self, view):
        self._view = view

    @property
    def func_name(self):
        """
        This is just a lame hack to get decent debug info from the lame default
        handler behaviour
        """
        name = repr(self.view)
        m = view_repr_pat.search(name)
        if m:
            return m.group(1)
        return name

    @property
    def view(self):
        if not hasattr(self, '_view_cache'):
            if isinstance(self._view, basestring):
                self._view_cache = get_view(self._view)
            else:
                self._view_cache = self._view
            update_wrapper(self, self._view_cache)
        return self._view_cache

    def __call__(self, request, *args, **kwargs):
        if hasattr(self.view, 'dispatch'):
            return self.view().dispatch(request, *args, **kwargs)
        elif callable(self.view):
            return self.view(request, *args, **kwargs)
        raise ImproperlyConfigured('%s.%s does not define a view function or '
            'class.' % (self.view.__module__, self.view.__name__)
            )


class RegexURLPattern(urlresolvers.RegexURLPattern):
    def __init__(self, regex, callback, default_args=None, name=None):
        self.regex = re.compile(regex, re.UNICODE)
        self._callback = callback
        self.default_args = default_args or {}
        self.name = name

    @property
    def callback(self):
        if not hasattr(self, '_callback_cache'):
            try:
                self._callback_cache = LazyView(self._callback)
            except Exception, e:
                raise urlresolvers.ViewDoesNotExist(e)
        return self._callback_cache


def include(arg, namespace=None, app_name=None):
    if isinstance(arg, tuple):
        # callable returning a namespace hint
        if namespace:
            raise ImproperlyConfigured(
                'Cannot override the namespace for a dynamic module that '
                'provides a namespace'
                )
        urlconf_module, app_name, namespace = arg
    else:
        # No namespace hint - use manually provided namespace
        urlconf_module = arg
    return (urlconf_module, app_name, namespace)


def patterns(prefix, *args):
    pattern_list = []
    for t in args:
        if isinstance(t, (list, tuple)):
            t = url(prefix=prefix, *t)
        elif isinstance(t, (RegexURLPattern, urlresolvers.RegexURLPattern)):
            t.add_prefix(prefix)
        pattern_list.append(t)
    return pattern_list


def url(regex, view, kwargs=None, name=None, prefix=''):
    if isinstance(view, (list, tuple)):
        # For include(...) processing.
        urlconf_module, app_name, namespace = view
        return urlresolvers.RegexURLResolver(regex, urlconf_module, kwargs,
            app_name=app_name, namespace=namespace
            )
    else:
        if isinstance(view, basestring):
            if not view:
                raise ImproperlyConfigured('Empty URL pattern view name not '
                    'permitted (for pattern %r)' % regex
                    )
            if prefix:
                view = '%s.%s' % (prefix, view)
        return RegexURLPattern(regex, view, kwargs, name)

