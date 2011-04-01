from django.shortcuts import render_to_response
from django.template import RequestContext
from utkik.decorators import http_methods


class ViewException(Exception):
    pass


class ContextData(object):
    """
    A container for attributes to store on the template context.

    All the attributes are later collected as a dictionary via ``__dict__``.
    """


class View(object):
    """
    A minimalist View base class.

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
    template_name = None # template name to render to

    def __init__(self):
        """
        Create a :class:`ContextData` instance for the view.
        """
        self.c = ContextData() # c is for context
        self.request = None

    def dispatch(self, request, *args, **kwargs):
        """
        View entry point.

        The utkik dispatcher will create a new instance of the current class
        and call this method when the Django handler makes a call to the view.
        """
        self.request = request
        return self._decorate(self.get_response)(request, *args, **kwargs)

    def _decorate(self, f):
        """
        Decorate a function with decorators from :attr:`decorators` and
        decorators based on :attr:`methods`.
        """
        for d in reversed(self.decorators):
            f = d(f)
        methods = [m for m in self.methods if hasattr(self, m.lower())]
        return http_methods(*methods)(f)

    def get_response(self, request, *args, **kwargs):
        """
        Return the response from a successful request to the view.

        Directs to a suitable handler method based on the HTTP method call.
        If this handler does not return a response, :meth:`render` is called
        and returned.

        Request is just passed in here for decorator compatibility.
        """
        try:
            return self.get_handler()(*args, **kwargs) or self.render()
        except Exception, e:
            raise ViewException("'%s.%s.get_response' failed: %s: %s" % (
                self.__module__, self.__class__.__name__,
                e.__class__.__name__, e))

    def get_handler(self):
        """
        Return the method for the current request.

        Override this to change the handler method that is used for a request,
        for example, to use an alternate handler for AJAX calls.
        """
        return getattr(self, self.request.method.lower())

    def get_context_data(self):
        """
        Return a dictionary containing the context data.

        Override this method to add to or modify the context data before it is
        used to render a template.

        This is called from :meth:`render`.
        """
        return self.c.__dict__

    def render(self):
        """
        Renders :meth:`self.template_name` using :meth:`get_context_data`.

        By default, this is called from :meth:`get_response` if the handler does
        not return a response.
        """
        return render_to_response(self.template_name,
            self.get_context_data(), RequestContext(self.request))

