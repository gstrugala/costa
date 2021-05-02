.. currentmodule:: fillomino.permapfiller
.. _api:

Fillomino reference
===================


The ``PermapFiller`` class
--------------------------
:class:`PermapFiller` extends the class :class:`pandas.DataFrame`
by `registering a DataFrame accessor`_ named ``pmf``.
Once Fillomino is imported, all PermapFiller methods and attributes
can be invoked by DataFrames in this way: ``df.pmf.normalized``.

.. autoclass:: PermapFiller
   :members:


The ``defaults`` module
-----------------------

.. automodule:: fillomino.defaults
   :members:

.. _registering a DataFrame accessor:
   https://pandas.pydata.org/pandas-docs/stable/development/extending.html#registering-custom-accessors
