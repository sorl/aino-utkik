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
This is the template that the ``render`` method will use to render to.

methods
-------

TODO make docstrings go here

