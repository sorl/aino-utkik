.. _reference:

*********
Reference
*********

BaseView
=========

attributes
----------

methods
^^^^^^^
This should contain a list of allowed HTTP methods for the view. The names
should be upper-case just as they are named in the HTTP spcification. If the
class has a method of the same name but in lower case this will be called to
when a request is made.

requires_ajax
^^^^^^^^^^^^^
Set this to ``True`` if you want to restrict the view to only ajax calls.

template
^^^^^^^^
This is the template that the ``render`` method will use to render to.

decorators
^^^^^^^^^^
A list of decorators applied in reverse order.


methods
-------

TODO make docstrings go here

