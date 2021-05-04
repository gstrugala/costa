.. currentmodule:: costa.permap
.. _api:

Costa reference
===================


The ``Permap`` class
--------------------
:class:`Permap` extends the class :class:`pandas.DataFrame`
by `registering a DataFrame accessor`_ named ``pm``.
Once Costa is imported, all Permap methods and attributes
can be invoked by DataFrames in this way: ``df.pm.normalized``.

.. autoclass:: Permap
   :members:


The ``defaults`` module
-----------------------

.. automodule:: costa.defaults
   :members:

.. _registering a DataFrame accessor:
   https://pandas.pydata.org/pandas-docs/stable/development/extending.html#registering-custom-accessors
