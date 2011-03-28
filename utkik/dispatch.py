import re
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core import urlresolvers
from django.utils.functional import update_wrapper, memoize
from django.utils.importlib import import_module


__all__ = ['handler404', 'handler500', 'include', 'patterns', 'url']


handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
view_repr_pat = re.compile(r"\.(\w+)'>$")
_view_cache = {} # memoize cache


def get_view(name):
    """Import and returns a view from string. You can use the full string path
    or a shorter notation ``myapp.ViewClass`` if ``myapp`` is in the list of
    ``INSTALLED_APPS``. We memoize the call to this function as it's unnecessary
    to resolve and import every time this is called with the same argument.
    """
    mod_name, attr = name.rsplit('.', 1)
    if mod_name in settings.INSTALLED_APPS:
        try:
            mod = import_module(mod_name + '.views')
            return getattr(mod, attr)
        except Exception:
            pass
    mod = import_module(mod_name)
    return getattr(mod, attr)
get_view = memoize(get_view, _view_cache, 1)


class LazyView(object):
    """Lazy import wrapper for a view function or class. This is what the
    Django handler will be calling.
    """
    def __init__(self, view):
        self._view = view
        self._view_cache = None

    @property
    def func_name(self):
        """This is just a lame hack to get decent debug info from the lame
        default handler behaviour.
        """
        name = repr(self.view)
        m = view_repr_pat.search(name)
        if m:
            return m.group(1)
        return name

    @property
    def view(self):
        """Return and cache the view from string or view class/function. Note
        that in the case of a view class that this is not an instance but the
        class, instantiation will be done in ``__call__`` method.
        """
        if self._view_cache is None:
            if isinstance(self._view, basestring):
                self._view_cache = get_view(self._view)
            else:
                self._view_cache = self._view
            # this is our first chance to update the wrapper
            update_wrapper(self, self._view_cache)
        return self._view_cache

    def __call__(self, request, *args, **kwargs):
        """In case of the wrapped view being determined as a class (that it has
        a dispatch attribute) we return a new instance of the class with all
        view arguments passed to the dispatch method. The case of a view
        function things are much simpler, we just call the view function with
        the view arguments.
        """
        if hasattr(self.view, 'dispatch'):
            return self.view().dispatch(request, *args, **kwargs)
        elif callable(self.view):
            return self.view(request, *args, **kwargs)
        raise ImproperlyConfigured('%s.%s does not define a view function or '
            'class.' % (self.view.__module__, self.view.__name__)
            )


class RegexURLPattern(urlresolvers.RegexURLPattern):
    def __init__(self, regex, callback, default_args=None, name=None):
        """We just changed the way the callback references are set compared to
        ``django.core.urlresolvers.RegexURLPattern.__init__``.
        """
        self.regex = re.compile(regex, re.UNICODE)
        self._callback = callback
        self._callback_cache = None
        self.default_args = default_args or {}
        self.name = name

    @property
    def callback(self):
        """This method is a little different from the default
        ``django.core.urlresolvers.RegexURLPattern.callback`` in that we return
        the callback wrapped in ``LazyView``.
        """
        if self._callback_cache is None:
            try:
                self._callback_cache = LazyView(self._callback)
            except Exception, e:
                raise urlresolvers.ViewDoesNotExist(e)
        return self._callback_cache


def include(arg, namespace=None, app_name=None):
    """Used to include another urls pattern file"""
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
    """Container for url regexp patterns"""
    pattern_list = []
    for t in args:
        if isinstance(t, (list, tuple)):
            t = url(prefix=prefix, *t)
        elif isinstance(t, (RegexURLPattern, urlresolvers.RegexURLPattern)):
            t.add_prefix(prefix)
        pattern_list.append(t)
    return pattern_list


def url(regex, view, kwargs=None, name=None, prefix=''):
    """sets up a regexp pattern for url processing"""
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

