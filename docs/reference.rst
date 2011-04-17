.. _reference:

*********
Reference
*********

View
====

attributes
----------

methods
^^^^^^^
This should contain a list of allowed HTTP methods for the view. The names
should be upper-case just as they are named in the HTTP spcification. If the
class has a method of the same name but in lower case this will be called to
when a request is made.

decorators
^^^^^^^^^^
A list of decorators applied to ``get_response``.

template_name
^^^^^^^^^^^^^
This is the template that the :meth:`render` will firstly try to render to. If
you don't set this or this template is not found :meth:`get_template_names` will
also return an automatically computed template name for you as: ``<< app_label
>>/<< un-cameled class name >>.html``.

ajax_template_name
^^^^^^^^^^^^^^^^^^
This does exactly as :attr:`template_name` but for ajax calls and the computed
template name is: ``<< app_label >>/<< un-cameled class name >>.ajax.html``.

methods
-------

TODO make docstrings go here

