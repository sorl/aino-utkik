import re
import sys
from django.conf import settings
from django.core import urlresolvers
from django.core.exceptions import ImproperlyConfigured
from functools import update_wrapper
from inspect import isclass
from utkik.utils import import_string, cached_property, uncamel


__all__ = ['handler404', 'handler500', 'include', 'patterns', 'url']


handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'


class UtkikException(Exception):
    pass


class ViewWrapper(object):
    """
    A view wrapper that makes function and class based views callable
    """

    def __init__(self, view):
        self.view = view
        if not hasattr(view, '__name__') and isinstance(view, object):
            # for class instances that use call
            view.__name__ = view.__class__.__name__
        update_wrapper(self, view)

    @property
    def func_name(self):
        """
        This is just a lame hack to get decent debug info from the lame default
        handler behaviour.
        """
        return self.__name__

    def __call__(self, request, *args, **kwargs):
        """
        In case of the wrapped view being determined as a class (that it has
        a dispatch attribute) we return a new instance of the class with all
        view arguments passed to the dispatch method. The case of a view
        function things are much simpler, we just call the view function with
        the view arguments.

        For debugging purposes we insert some additional information that is
        useful for view classes in the raised exception.
        """
        try:
            if isclass(self.view):
                view = self.view()
                if hasattr(view, 'dispatch'):
                    return view.dispatch(request, *args, **kwargs)
            else:
                view = self.view
            if callable(view):
                return view(request, *args, **kwargs)
        except Exception, ex:
            try:
                cls, e, trace = sys.exc_info()
                msg = '%s in %s.%s: %s' % (
                    cls.__name__, self.view.__module__, self.view.__name__, e
                    )
            except Exception:
                raise ex
            else:
                raise UtkikException(msg), None, trace
        raise ImproperlyConfigured('%s.%s does not define a view function or '
            'class view.' % (self.view.__module__, self.view.__name__))

    def __getattr__(self, name):
        return getattr(self.view, name)


class LazyViewWrapper(ViewWrapper):
    """
    Lazy import wrapper for a view function or class.
    """

    def __init__(self, dot_name):
        module, name = dot_name.rsplit('.', 1)
        if module in settings.INSTALLED_APPS:
            module += '.views'
        self.__module__ = module
        self.__name__ = name
        self.dot_name = '%s.%s' % (module, name)

    @cached_property
    def view(self):
        """
        Return and cache the view from string. Note that in the case of a
        view class that this is not an instance but the class, instantiation
        will be done in the ``__call__`` method.
        """
        view = import_string(self.dot_name)
        self.__doc__ = view.__doc__
        return view


class RegexURLPattern(urlresolvers.RegexURLPattern):
    def __init__(self, regex, callback, default_args=None, name=None):
        """
        We just changed the way the callback references are set compared to
        ``django.core.urlresolvers.RegexURLPattern.__init__``.
        """
        self.regex = re.compile(regex, re.UNICODE)
        self._callback = callback
        self.default_args = default_args or {}
        self.name = name

    def add_prefix(self, prefix):
        """
        Adds the prefix string to a string-based callback.
        """
        if prefix and isinstance(self._callback, basestring):
            self._callback = '%s.%s' % (prefix, self._callback)

    @cached_property
    def callback(self):
        """
        This method is a little different from the default
        ``django.core.urlresolvers.RegexURLPattern.callback`` in that we return
        the callback wrapped in a ``ViewWrapper`` or ``LazyViewWrapper``.
        """
        try:
            if isinstance(self._callback, basestring):
                return LazyViewWrapper(self._callback)
            return ViewWrapper(self._callback)
        except Exception, e:
            raise urlresolvers.ViewDoesNotExist(e)


def include(arg, namespace=None, app_name=None):
    """
    Used to include another urls pattern file
    """
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
    """
    Container for url regexp patterns
    """
    pattern_list = []
    for t in args:
        if isinstance(t, (list, tuple)):
            t = url(prefix=prefix, *t)
        elif isinstance(t, (RegexURLPattern, urlresolvers.RegexURLPattern)):
            t.add_prefix(prefix)
        pattern_list.append(t)
    return pattern_list


def url(regex, view, kwargs=None, name=None, prefix=''):
    """
    sets up a regexp pattern for url processing
    """
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
            if name is None:
                name = uncamel(view.split('.')[-1])
        return RegexURLPattern(regex, view, kwargs, name)

