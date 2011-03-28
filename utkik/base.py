from django.http import HttpResponse
from django.shortcuts import render


class ViewException(Exception):
    pass


class Context(object):
    pass


class BaseView(object):
    """
    View base class.
    """

    allowed_methods = ['GET', 'POST']
    requires_ajax = False
    c = None # c is for context
    template = None
    content_type = None
    status = None
    context_instance = None
    current_app = None

    def __init__(self):
        self.c = Context()

    def dispatch(self, request, *args, **kwargs):
        """
        View entry point
        """
        self.request = request
        return self.get_error_response() or self.get_response(*args, **kwargs)

    def get_error_response(self):
        if self.request.method in self.allowed_methods:
            if not hasattr(self, self.request.method.lower()):
                return HttpResponse(status=405)
        if self.requires_ajax and not self.request.is_ajax():
            return HttpResponse(status=403)

    def get_response(self, *args, **kwargs):
        response = self.get_handler()(*args, **kwargs)
        if response is None:
            return self.render()
        return response

    def get_handler(self):
        name = self.request.method.lower()
        return getattr(self, name)

    def get_context(self):
        return self.c.__dict__

    def render(self):
        """
        Renders a given context to template
        """
        if not self.template:
            raise ViewException(
                _('%s does not define a template to render to.') % self
                )
        params = {
            'content_type': self.content_type,
            'status': self.status,
            'current_app': self.current_app,
        }
        if self.context_instance is not None:
            params['context_instance'] = self.context_instance
        return render(self.request, self.template, self.get_context(), **params)

