.. _api:

Fillomino reference
===================

.. automodule:: fillomino
   :members:


The ``PermapFiller`` class
--------------------------
``PermapFiller`` extends the `pandas.DataFrame`_ class
by registering a dataframe accessor named ``pmf``.
Once Fillomino is imported, all ``PermapFiller`` methods and attributes
can be invoked by dataframes in this way: ``df.pmf.normalized``.


.. autoclass:: fillomino.permapfiller.PermapFiller
   :members:

The ``defaults`` module
-----------------------

.. automodule:: fillomino.defaults
   :members:


.. _pandas.DataFrame: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html
