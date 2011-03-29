from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _


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
    c = None # c is for context
    template = None # template to render to

    def __init__(self):
        """All we do here is to instantiate the Context class"""
        self.c = Context()
        self.request = None

    def dispatch(self, request, *args, **kwargs):
        """View entry point. The utkik dispatcher will create a new instance of
        the current class and call this method when the Django handler makes a
        call to the view.
        """
        self.request = request
        return self.get_error_response() or self.get_response(*args, **kwargs)

    def get_error_response(self):
        """This should return a suitable response when requirements are not
        met, for example when the view is called with a method not supported or
        when ``self.requires_ajax`` is set to ``True`` and the request is not
        an ajax request.
        """
        if self.request.method in self.allowed_methods:
            if not hasattr(self, self.request.method.lower()):
                return HttpResponse(status=405)
        if self.requires_ajax and not self.request.is_ajax():
            return HttpResponse(status=403)

    def get_response(self, *args, **kwargs):
        """Returns the response from a successful request to the view. In it's
        default implementation it will direct to a suitable handler method
        based on the HTTP method call. If this handler does not return a
        response, we will simply call and return ``self.render``.
        """
        response = self.get_handler()(*args, **kwargs)
        if response is None:
            return self.render()
        return response

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
        Renders ``self.get_context()`` to ``self.template`` using the shortcut
        from ``django.shortcuts.render`` function. This is called from
        ``self.get_response`` if the handler does not return a response. There
        is not much going on in this method, we make sure there is a template
        defined, then we render the context while adding some keyword arguments
        to the render function.
        """
        if not self.template:
            raise ViewException(
                _('%s does not define a template to render to.') % self
                )
        return render(self.request, self.template, self.get_context())

