from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from utkik.decorators import http_methods


class ViewException(Exception):
    pass


class ContextData(object):
    """This will contain attributes for context. All the attributes are later
    collected by ContextData().__dict__.
    """


class View(object):
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

    methods = ['GET', 'POST'] # allowed HTTP methods
    decorators = [] # a list of decorators
    template = None # template to render to

    def __init__(self):
        """All we do here is to instantiate the ContextData class"""
        self.c = ContextData() # c is for context
        self.request = None

    def dispatch(self, request, *args, **kwargs):
        """View entry point. The utkik dispatcher will create a new instance of
        the current class and call this method when the Django handler makes a
        call to the view.
        """
        self.request = request
        return self._decorate(self.get_response)(request, *args, **kwargs)

    def _decorate(self, f):
        """This is meant to decorate ``self.get_response`` with
        ``self.decorators`` much like you would decorate a view function (if you
        remember that era). There is one decorator automatically added here and
        that is the ``http_methods`` computed decorator that uses
        ``self.methods`` attribute and avalable handlers to define what methods
        are allowed.
        """
        for d in reversed(self.decorators):
            f = d(f)
        methods = [m for m in self.methods if hasattr(self, m.lower())]
        return http_methods(*methods)(f)

    def get_response(self, request, *args, **kwargs):
        """Returns the response from a successful request to the view. In it's
        default implementation it will direct to a suitable handler method based
        on the HTTP method call. If this handler does not return a response, we
        will simply call and return ``self.render``. Request is just passed in
        here for decorator compatibilty reasons, don't use it, don't get
        confused by it, just use ``self.request``.
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

    def render(self, template=None):
        """
        Renders ``self.get_context()`` to ``self.template`` or a template
        argument. This is called from ``self.get_response`` if the handler does
        not return a response.
        """
        template = template or self.template
        if not template:
            raise ViewException(_('Missing template to render to.'))
        return render_to_response(
            template, self.get_context(), RequestContext(self.request))

