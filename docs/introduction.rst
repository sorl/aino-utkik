.. _introduction:

Introduction
============

The past
--------
We are lazy and we should be. Class based views has been a long time itch for
us Django users. There are a lot good use-cases for using classes for your views
instead of functions. The first that come in to mind is probably inheritance,
define a view and then re-use some of that code for another view without having
to completely rewrite it, that's great right? For example::

    class MyBaseView(object):
        def get_queryset(self):
            raise NotImplemented

        def do_something_useful(self):
            qs = self.get_queryset()
            ...

    class MyView(MyBaseView):
        def get_queryset(self):
            return MyModel.objects.all()

For Django users this was a bit hard to solve since the view had to be a
callable in the current infrastructure. Some people started out creating class
based views using the ``__call__`` method of a class like this::

    class OopsView(object)
        def __call__(self, request):
            self.request = request

        def render(self):
            return response

And with something like this in urls.py::

    from django.conf.urls.defaults import *
    from oops.views import OopsView

    urlpatterns = patterns('',
        (r'^$', OopsView()),
    )

The problem with this approach is that you are creating an instance of the class
in urls and then you are setting a state to it in ``self.request = request``
effectively making the view one instance sharing it's state across requests. All
kinds of solutions exists to solve this problem, they can be divided into two
different approaches, the first that does not store state that changes across
requests (used by ``django.contrib.admin``) which requires you to pass things
like request around and the second implementation is to create a new instance on
every request. The latter being more safe and you do not have to worry about
sharing state since every request will have their own class instance. Django
adopted class based views for 1.3 generic views using the second approach. The
way its done is by having a class method on the view class that returns a
function (callable) that returns a class instance and calling the instances
entry point (dispatch). To use a class based view subclassed from
``django.views.generic.View`` you now call the class method ``as_view`` in your
urls.py::

    from django.conf.urls.defaults import *
    from myapp.views import MyView

    urlpatterns = patterns('',
        (r'^$', MyView.as_view()),
    )

This works fine except for a few things:

    1. If there is an import error in urls.py you will have a very hard time to
       debug it.
    2. The urls.py can get really cluttered with view imports.
    3. Writing ``.as_view()`` that many times is really boring and is a weird
       redundant suffix.


The future
----------
What I would like to be able to do is more something like::

    from django.conf.urls.defaults import *

    urlpatterns = patterns('',
        (r'^$', 'myapp.MyView'),
    )

Now ``myapp.MyView`` is not a correct "python string notation" as would probably
be ``myapp.views.MyView``, did I say I was lazy? After all a string is not
python is it? This would solve all of the things listed above:

    1. We would have lazy imports, working out the view first when it is called.
       Getting a proper traceback in case something goes wrong, well hopefully.
    2. We don't need to do all those imports into urls.py
    3. Less writing is good as long as it is explicit.

So how can we achieve something like this?

    1. If we are good with using ``myapp.views.MyView`` then we can hack
       something together using metaclasses and what not in the view class. Or
       we can change the handler.
    2. We change the behaviour of the ``django.conf.urls.defaults.url``
       function.
    3. Change the handler to not just accept a callable in addition to #2.

As for changing the handler, let's just say that I rather not. I figured #3
would be the best solution but that is more work than #2, did I say I was lazy?
``utkik.dispatch.url`` is class based view aware. The modification was not very
big nor hard, have a look in the source code. To outline the basic idea, we
create a class called ``LazyView`` that wraps the view, be it a class view or a
function view string notated or not and when that class instance is called
(``__call__``) on from the django handler it will either return the view
function call or create a new instance of the class view and calling its entry
point (dispatch).


I can't stop
------------
It's great now we have a nice way to route to class based views. The next topic
is class based views. What do we want them to do and how do we want to work with
them? Here is an unordered in terms of importance wish list of things I would
like to see:

    1. Catch bad requests and return a proper error code.
    2. Render a certain template with context using very little code.
    3. Make it easy to update the current context for the template rendering.
    4. Have sensible hooks for subclassing.
    5. Subclasses should be easy to read and follow.
    6. They should be very convenient but allow for special cases without
       breaking a sweat.
    7. Embrace the instance state when you need to, now that you have it.
    8. Reading the source code should be easy.

Of course I am just listing all those things that match what my current
implementation has, I just do that to make me look good. Django 1.3 class based
generic views certainly does some of these things but unfortunately some out
right not. This is just speaking from a general class based view point not
taking the generic part into account. Beware that this means I am not totally
fair since the generic views will have problems to share my goals with the other
goals set for them. So how does Django 1.3 class-based generic views stack up?

    1. Catch bad requests and return a proper error code.

       Yes, but only partially, the default behaviour is to allow every HTTP
       method if it has such a lowercase attribute of the class. I would say it
       is a rare use-case for anything else but GET/POST, something could
       definitely go wrong there. It does not check for ajax at all.

    2. Render a certain template with context using very little code.

       This it can achieve very well, although you need the docs around to
       remember the method and variable names to set.

    3. Make it easy to update the current context for the template rendering.

       Well it's not hard but still not quite there, there is a method called
       ``get_context_data`` Is this where you should get all your context data?
       In my mind that is mostly what a view does in a typical case, It collects
       data for the context that it used to render the template with. I guess
       this is where most of your code will end up unless you do something
       creative.

    4. Have sensible hooks for subclassing.

       I think the dispatch method could be divided into smaller parts to better
       allow subclassing, for the more specialized generic cases I do not know.

    5. Subclasses should be easy to read and follow.

       See 6

    6. They should be very convenient but allow for special cases without
       breaking a sweat.

       Granted, they are convenient, but they still suffer from what we had from
       the old function based generic views. When you want to do something a
       little different, it's hard, so hard you need to read the source. When
       you read the source you also notice its full of nice mixins. Mixins are
       great but it makes it very hard to follow and you sort of have to
       construct that final class in your head, tricky for sure. Anyway, once
       you managed to get that class doing what you wanted you realize that it
       is very hard to follow as well, let alone remember.

    7. Embrace the instance state when you need to, now that you have it.

       Why is request the first argument of the handlers? First you read in the
       dispatch method ``self.request = request`` and then ``handler(request,
       *args, **kwargs)``. Maybe I am missing something here but this is just
       confusing. To me it should read: ``handler(*args, **kwargs)`` and the
       first argument in the handler should not be request but the arguments and
       Keyword arguments kwargs parsed from urls. Arguments and Keyword
       arguments are stored in the instance as ``self.args`` and
       ``self.kwargs``, Personally I have a problem with the naming and secondly
       when do we need to access those in anything but the handlers? If we find
       cases to reference those attributes it will be very hard to understand
       what is happening.

    8. Reading the source code should be easy.
    
       It is just not because of all the generalizations and mixins.

.. _whoami:

Who are you?
------------
I am a minimalist class based view base class for Django (MCBVBCFD) as seen on
TV::

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
        template = None # template to render to

        def __init__(self):
            """All we do here is to instantiate the Context class"""
            self.c = Context() # c is for context
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

