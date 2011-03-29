.. _quickstart:

Quickstart
==========

Requirements, Installation & Configuration
------------------------------------------
.. note:: You need Django 1.3+

Firstly install the package from pypi::

    pip install aino-utkik

Secondly, you need to setup the dispatcher by replacing all imports in all your
urls.py. Before::

    from django.conf.urls.defaults import

After::
    
    from utkik.dispatch import

Anything after the ``import`` on the same row should be kept intact.
If you are brave you can place your self in your project root and issue::

    find -name urls.py | xargs perl -p -i -e 's/from\ django\.conf\.urls.defaults/from utkik.dispatch/g'


Usage
-----

Dispatcher
^^^^^^^^^^
Now you are ready to use the utkik dispatcher. This allows you to reference a
class based view based from Django 1.3 Class-based generic views or
``utkik.BaseView`` as a string in your urls.py (or any other class based view
that has an entry point method called dispatch). Assuming that your class
resides in ``myapp.views.Home`` and that ``myapp`` is in ``INSTALLED_APPS`` you
may reference it as follows::

    from utkik.dispatch import *

    urlpatterns = patterns('',
        (r'^$', 'myapp.Home'),
    )

Alternatively you can reference it with a more accurate string. You can always
reference a class based view even if it's not in ``INSTALLED_APPS`` this way::

    from utkik.dispatch import *

    urlpatterns = patterns('',
        (r'^$', 'myapp.views.Home'),
    )


utkik.BaseView
^^^^^^^^^^^^^^
I will describe the main ideas here and if you have the time please look through
the :ref:`source code <whoami>`, it is really small.

Firstly the *handler* for an allowed request is defined as a method that has the
same name as the HTTP request method, only lower cased. So a GET request will
try to call a get method on the class and a POST method a post and so on. A
method is allowed only if the class has a corresponding lower case named
attribute on the class. But because not everyone keeps those method names in
their head there is an additional attribute in the class that controls if the
method should be allowed or not and that is ``allowed_methods``. By default this
is set to ``['GET', 'POST']`` thus allowing only GET and POST. If you want to
allow anything else you first have to add that method name to this list and then
create a method with the lower case name on the class.

So basically you do all your stuff in the handler or conduct it from there, for
example ``MyView.get``.  The handler gets passed any additional arguments that
is parsed from the urls.py but not the request. The request object is accessed
through the class instance it self ``self.request``. So your get handler might
start something like::

    def get(self, slug):
        ...

At the end of the handler you can either return a valid ``HttpResponse`` or you
don't return anything. If you don't return anything the ``self.render`` method
will be called. This method essentially renders ``self.template`` with
``self.get_context`` as context using ``django.shortcuts.render`` and returns
the result.

But wait there is more! In your view you can reference an object
representing the context as ``self.c``. You can set stuff to the context as
follows::

    self.c.news = get_object_or_404(News.objects, slug=slug)

The ``self.get_context`` by default returns this context object as a dictionary.
Lest bake a simple view from all this::

    from utkik import BaseView
    from news.models import News

    class NewsView(BaseView):
        template = 'news/news_detail.html'

        def get(self, slug):
            self.c.news = get_object_or_404(News.objects, slug=slug)

That is all there is to it! You are not returning anything from the handler and
thus letting ``self.render`` do the work.


For more please :ref:`read the code <whoami>` and see the :ref:`examples <compare>`.

