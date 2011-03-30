from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from utkik.decorators import requires_ajax, allowed_methods, decorate


class ViewException(Exception):
    pass


class Context(object):
    """This will contain attributes for context. All the attributes are later
    collected by Context().__dict__.
    """


class BaseView(object):
    """A minimalist View base class.

    Goals
    -----
    - Building context for rendering should be simple.

    - Source should be easy to follow and encourage this for implementing
      subclasses if possible.

    - Keep methods short and provide useful hooks for sub classing.

    - Embrace the instance and don't pass request nor context around.

    - Narrow the scope to most common use but without limiting less usual
      use-cases.
    """

    allowed_methods = ['GET', 'POST'] # allowed HTTP methods
    requires_ajax = False # force ajax
    template = None # template to render to
    decorators = [] # a list of decorators applied in reverse order

    def __init__(self):
        """All we do here is to instantiate the Context class"""
        self.c = Context() # c is for context
        self.request = None

    def dispatch(self, request, *args, **kwargs):
        """View entry point. The utkik dispatcher will create a new instance of
        the current class and call this method when the Django handler makes a
        call to the view. We get all the decorators using the list returned
        ``self._get_decorators`` and decorate the ``self.get_response`` method
        with those decorators.
        """
        self.request = request
        return decorate(self._get_decorators())(self.get_response)(
            request, *args, **kwargs
            )

    def _get_decorators(self):
        """Returns a list of decorators, The first part of the list are
        decorators in ``self.decorators`` which are the user defined decorators.
        The second part of this list are decorators that enforces ajax if
        ``self.requires_ajax`` is ``True`` and a decorator that makes sure the
        current request HTTP method is allowed.
        """
        decorators = list(self.decorators)
        if self.requires_ajax:
            decorators.append(requires_ajax)
        methods = [m for m in self.allowed_methods if hasattr(self, m.lower())]
        decorators.append(allowed_methods(methods))
        return decorators

    def get_response(self, request, *args, **kwargs):
        """Returns the response from a successful request to the view. In it's
        default implementation it will direct to a suitable handler method
        based on the HTTP method call. If this handler does not return a
        response, we will simply call and return ``self.render``. Request is
        only passed in here for decorator compatibility reasons.
        """
        return self.get_handler()(*args, **kwargs) or self.render()

    def get_handler(self):
        """Return a suitable handler. You can override this for example if you
        want another handler for ajax calls.
        """
        return getattr(self, self.request.method.lower())

    def get_context(self):
        """If you want to add some extra context or modify the current context
        this is a good place. This method is called from ``self.render``.
        """
        return self.c.__dict__

    def render(self):
        """
        Renders ``self.get_context()`` to ``self.template``. This is called from
        ``self.get_response`` if the handler does not return a response.
        """
        if not self.template:
            raise ViewException(
                _('%s does not define a template to render to.') % self)
        return render_to_response(
            self.template, self.get_context(), RequestContext(self.request))

