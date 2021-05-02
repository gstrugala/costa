.. currentmodule:: fillomino.permapfiller

.. define non-breaking space by |_|
.. |_| unicode:: 0xA0
   :trim:


Modifying the performance map
=============================

By extending the :class:`~pandas.DataFrame` class, :class:`PermapFiller`
objects can modify their data and perform powerful operations quite easily.
Below are some tips that could prove useful to those users who wish to process
performance table data using :mod:`pandas` methods.


Keep ``pmf`` attributes: the :meth:`~PermapFiller.copyattr` method
------------------------------------------------------------------

Many DataFrame methods works by returning a new instance instead of modifying
the DataFrame itself. However, when using such methods the returned new
instance does not remember the attributes in the ``pmf`` namespace.
For example, consider the following performance map.
(Without arguments, the method :meth:`~fillomino.build_heating_permap` use
by default the performance table shown in the :ref:`quick tutorial <tuto>`.)

.. ipython::

   In [1]: import fillomino

   In [2]: hpm = fillomino.build_heating_permap()

   In [3]: hpm
   Out[3]: heating     capacity  power
   Tdbr Tdbo
   15.6 -26.1      3.62   2.15
        -20.6      4.63   2.16
        -15.0      5.11   2.17
        -10.0      5.36   2.13
        -5.0       5.86   2.10
         0.0       6.03   2.07
         5.0       6.58   1.88
         8.3       6.80   1.86
         10.0      7.52   1.85
         15.0      7.79   1.64
   18.3 -26.1      3.54   2.19
        -20.6      4.52   2.20
        -15.0      4.99   2.21
        -10.0      5.23   2.18
        -5.0       5.72   2.14
         0.0       5.88   2.11
         5.0       6.43   1.92
         8.3       6.64   1.90
         10.0      7.34   1.89
         15.0      7.60   1.68
   21.1 -26.1      3.45   2.23
        -20.6      4.41   2.24
        -15.0      4.86   2.25
        -10.0      5.10   2.22
        -5.0       5.58   2.18
         0.0       5.74   2.15
         5.0       6.27   1.96
         8.3       6.48   1.94
         10.0      7.16   1.93
         15.0      7.42   1.71
   23.9 -26.1      3.28   2.31
        -20.6      4.19   2.32
        -15.0      4.62   2.34
        -10.0      4.85   2.30
        -5.0       5.30   2.26
         0.0       5.45   2.23
         5.0       5.96   2.04
         8.3       6.15   2.02
         10.0      6.80   2.00
         15.0      7.05   1.78

   In [4]: hpm.pmf.mode = 'heating'

   In [5]: hpm.pmf.mode
   Out[5]: 'heating'

Assume that we want to get another DataFrame with a different index hierarchy,
where ``Tdbo`` is the leftmost level. This can be done for example using
the pandas methods :meth:`~pandas.DataFrame.reorder_levels` and
:meth:`~pandas.DataFrame.sort_index`.

.. ipython::

   In [6]: hpm2 = hpm.reorder_levels(['Tdbo', 'Tdbr']).sort_index()

   In [7]: hpm2
   Out[7]:
   heating     capacity  power
   Tdbo  Tdbr
   -26.1 15.6      3.62   2.15
         18.3      3.54   2.19
         21.1      3.45   2.23
         23.9      3.28   2.31
   -20.6 15.6      4.63   2.16
         18.3      4.52   2.20
         21.1      4.41   2.24
         23.9      4.19   2.32
   -15.0 15.6      5.11   2.17
         18.3      4.99   2.21
         21.1      4.86   2.25
         23.9      4.62   2.34
   -10.0 15.6      5.36   2.13
         18.3      5.23   2.18
         21.1      5.10   2.22
         23.9      4.85   2.30
   -5.0  15.6      5.86   2.10
         18.3      5.72   2.14
         21.1      5.58   2.18
         23.9      5.30   2.26
    0.0  15.6      6.03   2.07
         18.3      5.88   2.11
         21.1      5.74   2.15
         23.9      5.45   2.23
    5.0  15.6      6.58   1.88
         18.3      6.43   1.92
         21.1      6.27   1.96
         23.9      5.96   2.04
    8.3  15.6      6.80   1.86
         18.3      6.64   1.90
         21.1      6.48   1.94
         23.9      6.15   2.02
    10.0 15.6      7.52   1.85
         18.3      7.34   1.89
         21.1      7.16   1.93
         23.9      6.80   2.00
    15.0 15.6      7.79   1.64
         18.3      7.60   1.68
         21.1      7.42   1.71
         23.9      7.05   1.78

Here, ``hpm`` and ``hpm2`` represent the same performance map,
but arranged in a different way.
It would make sense that ``hpm2`` retain attributes from ``hpm``,
such as the operating mode that was set to ``'heating'``.
However, this is not the case:

.. ipython::

   In [8]: hpm2.pmf.mode is None
   Out[8]: True

To keep the attributes, you can use the method :meth:`~PermapFiller.copyattr`
on the new instance returned by the pandas methods.

.. ipython::

   In [8]: hpm2 = hpm.reorder_levels(['Tdbo', 'Tdbr']).sort_index().pmf.copyattr(hpm)

   In [9]: hpm2.pmf.mode
   Out[9]: 'heating'


.. _norm:

Normalize data: the :meth:`~PermapFiller.normalize` method
----------------------------------------------------------

Performance tables often output non-normalized values. Users may therefore want
to normalize the data, especially since it is required in the Type |_| 3254.
Of course, it is pretty easy using pandas. If we take the ``hpm`` table from
the previous example, and assume a rated capacity and rated power of 4.69 |_| W
and 1.01 |_| W respectively, one could just do:

.. ipython::

   In [9]: hpm_norm = hpm.pmf.copy()

   In [10]: hpm_norm['capacity'] = hpm_norm.capacity / 4.69

   In [11]: hpm_norm['power'] = hpm_norm.power / 1.01

   In [12]: hpm_norm
   Out[12]:
   heating     capacity     power
   Tdbr Tdbo
   15.6 -26.1  0.771855  2.128713
        -20.6  0.987207  2.138614
        -15.0  1.089552  2.148515
        -10.0  1.142857  2.108911
        -5.0   1.249467  2.079208
         0.0   1.285714  2.049505
         5.0   1.402985  1.861386
         8.3   1.449893  1.841584
         10.0  1.603412  1.831683
         15.0  1.660981  1.623762
   18.3 -26.1  0.754797  2.168317
        -20.6  0.963753  2.178218
        -15.0  1.063966  2.188119
        -10.0  1.115139  2.158416
        -5.0   1.219616  2.118812
         0.0   1.253731  2.089109
         5.0   1.371002  1.900990
         8.3   1.415778  1.881188
         10.0  1.565032  1.871287
         15.0  1.620469  1.663366
   21.1 -26.1  0.735608  2.207921
        -20.6  0.940299  2.217822
        -15.0  1.036247  2.227723
        -10.0  1.087420  2.198020
        -5.0   1.189765  2.158416
         0.0   1.223881  2.128713
         5.0   1.336887  1.940594
         8.3   1.381663  1.920792
         10.0  1.526652  1.910891
         15.0  1.582090  1.693069
   23.9 -26.1  0.699360  2.287129
        -20.6  0.893390  2.297030
        -15.0  0.985075  2.316832
        -10.0  1.034115  2.277228
        -5.0   1.130064  2.237624
         0.0   1.162047  2.207921
         5.0   1.270789  2.019802
         8.3   1.311301  2.000000
         10.0  1.449893  1.980198
         15.0  1.503198  1.762376

However using the method :meth:`~PermapFiller.normalize`
is more straightforward:

.. ipython::

   In [13]: import pandas as pd

   In [14]: rated_values = pd.DataFrame({'capacity': [4.69], 'power': [1.01]})

   In [15]: hpm_norm = hpm.pmf.normalize(values=rated_values)

   In [16]: hpm_norm
   Out[16]:
   heating     capacity     power
   Tdbr Tdbo
   15.6 -26.1  0.771855  2.128713
        -20.6  0.987207  2.138614
        -15.0  1.089552  2.148515
        -10.0  1.142857  2.108911
        -5.0   1.249467  2.079208
         0.0   1.285714  2.049505
         5.0   1.402985  1.861386
         8.3   1.449893  1.841584
         10.0  1.603412  1.831683
         15.0  1.660981  1.623762
   18.3 -26.1  0.754797  2.168317
        -20.6  0.963753  2.178218
        -15.0  1.063966  2.188119
        -10.0  1.115139  2.158416
        -5.0   1.219616  2.118812
         0.0   1.253731  2.089109
         5.0   1.371002  1.900990
         8.3   1.415778  1.881188
         10.0  1.565032  1.871287
         15.0  1.620469  1.663366
   21.1 -26.1  0.735608  2.207921
        -20.6  0.940299  2.217822
        -15.0  1.036247  2.227723
        -10.0  1.087420  2.198020
        -5.0   1.189765  2.158416
         0.0   1.223881  2.128713
         5.0   1.336887  1.940594
         8.3   1.381663  1.920792
         10.0  1.526652  1.910891
         15.0  1.582090  1.693069
   23.9 -26.1  0.699360  2.287129
        -20.6  0.893390  2.297030
        -15.0  0.985075  2.316832
        -10.0  1.034115  2.277228
        -5.0   1.130064  2.237624
         0.0   1.162047  2.207921
         5.0   1.270789  2.019802
         8.3   1.311301  2.000000
         10.0  1.449893  1.980198
         15.0  1.503198  1.762376

Moreover, it keeps track that ``hpm_norm`` was normalized,
and prevents normalizing more than once by mistake.
Normalization can also be performed implicitly by giving the ``rated_values``
as the ``norm`` argument of the :meth:`~PermapFiller.fill` method
(see :ref:`filling the performance map <fill pm>`).
