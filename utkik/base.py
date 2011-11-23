from django.shortcuts import render_to_response
from django.template import RequestContext
from utkik.decorators import http_methods
from utkik.utils import uncamel


class ContextData(object):
    """
    A container for attributes to store on the template context.

    All the attributes are later collected as a dictionary via ``__dict__``.
    """


class View(object):
    """
    aino-utkik Goals
    ----------------
    - Building context for rendering should be simple.

    - Source should be easy to follow and encourage this for implementing
      subclasses if possible.

    - Keep methods short and provide useful hooks for sub classing.

    - Embrace the instance and don't pass request nor context around.

    - Narrow the scope to most common use but without limiting less usual
      use-cases.

    - We don't like super. We want common View subclasses without the need for
      super.

    - Strong convention over configuration, close to magic.
    """
    methods = ['GET', 'POST', 'PUT', 'DELETE'] # allowed HTTP methods
    decorators = [] # a list of decorators
    template_name = None # template name to render to
    ajax_template_name = None # template name to render to for ajax calls

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
        Request is just passed in here for decorator compatibility.

        First :meth:`setup` is called, mostly used for context to be accessed
        across different methods. Then we get the response from suitable
        handler method based on the HTTP method call. By default the handler is
        already checked for existense in :meth:`_decorate`. If the handler does
        not return a response, :meth:`render` is called and returned.
        """
        self.setup(*args, **kwargs)
        handler = getattr(self, self.request.method.lower())
        return handler(*args, **kwargs) or self.render()

    def setup(self, *args, **kwargs):
        """
        This is where you would put code that is the same for different
        handlers. For example if you wanted to update template context data for
        both POST and GET methods in the same way::

            self.c.form = Form(data=self.request.POST or None)

        """

    def get_context_data(self):
        """
        Return a dictionary containing the context data.

        Override this method to add to or modify the context data before it is
        used to render a template.

        This is called from :meth:`render`.
        """
        return self.c.__dict__

    def get_template_names(self):
        """
        Returns list of template names to be used for the request. Used by
        :meth:`render`.
        """
        for dirname in reversed(self.__module__.split('.')):
            if dirname != 'views':
                break
        fmt = dirname, uncamel(self.__class__.__name__)
        template_names = [ self.template_name, u'%s/%s.html' % fmt ]
        if self.request.is_ajax():
            template_names = [ self.ajax_template_name,
                u'%s/%s.ajax.html' % fmt ] + template_names
        return [ t for t in template_names if t ]

    def render(self, template_name=None):
        """
        Renders :meth:`self.get_template_names` using :meth:`get_context_data`,
        alternatively renders a provided `template_name` template.

        By default, this is called from :meth:`get_response` if the handler does
        not return a response.
        """
        return render_to_response(template_name or self.get_template_names(),
            self.get_context_data(), RequestContext(self.request))

