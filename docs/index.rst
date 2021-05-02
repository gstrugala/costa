.. define non-breaking space by |_|
.. |_| unicode:: 0xA0
   :trim:


Fillomino: make the most of your performance data
=================================================

Fillomino is a Python package aiming to fill incomplete performance maps
using correction curves.
**It is meant to create variable capacity air-to-air heat pumps performance maps
that can be used by the** `Type 3254`_ **in TRNSYS.**
Below is a :ref:`quick tutorial <tuto>` showing Fillomino's basic usage.
You can also check out the :ref:`installation instructions <installation>`,
and more in-depth features.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   permap/load
   permap/modify
   permap/extend
   permap/write
   Fillomino API reference <api>


.. _tuto:

Quick tutorial: filling a heating performance table
---------------------------------------------------

Let's assume that we have the following performance map,
giving values (in watts) of the total capacity (TC) and input power (IP)
under different temperature conditions. Both frequency and air flow rate
entries are missing to get a complete table required for the Type |_| 3254.
This tutorial shows how to build such a table step by step.

+-----------------+-------------+-------------+-------------+-------------+
| :math:`T_{dbr}` | 15.6 °C     | 18.3 °C     | 21.1 °C     | 23.9 °C     |
+-----------------+------+------+------+------+------+------+------+------+
| :math:`T_{dbo}` | TC   | IP   | TC   | IP   | TC   | IP   | TC   | IP   |
+=================+======+======+======+======+======+======+======+======+
| **–26.1 °C**    | 3.62 | 2.15 | 3.54 | 2.19 | 3.45 | 2.23 | 3.28 | 2.31 |
+-----------------+------+------+------+------+------+------+------+------+
| **–20.6 °C**    | 4.63 | 2.16 | 4.52 | 2.20 | 4.41 | 2.24 | 4.19 | 2.32 |
+-----------------+------+------+------+------+------+------+------+------+
| **–15 °C**      | 5.11 | 2.17 | 4.99 | 2.21 | 4.86 | 2.25 | 4.62 | 2.34 |
+-----------------+------+------+------+------+------+------+------+------+
| **–10 °C**      | 5.36 | 2.13 | 5.23 | 2.18 | 5.10 | 2.22 | 4.85 | 2.30 |
+-----------------+------+------+------+------+------+------+------+------+
| **–5 °C**       | 5.86 | 2.10 | 5.72 | 2.14 | 5.58 | 2.18 | 5.30 | 2.26 |
+-----------------+------+------+------+------+------+------+------+------+
| **0 °C**        | 6.03 | 2.07 | 5.88 | 2.11 | 5.74 | 2.15 | 5.45 | 2.23 |
+-----------------+------+------+------+------+------+------+------+------+
| **5 °C**        | 6.58 | 1.88 | 6.43 | 1.92 | 6.27 | 1.96 | 5.96 | 2.04 |
+-----------------+------+------+------+------+------+------+------+------+
| **8.3 °C**      | 6.80 | 1.86 | 6.64 | 1.90 | 6.48 | 1.94 | 6.15 | 2.02 |
+-----------------+------+------+------+------+------+------+------+------+
| **10 °C**       | 7.52 | 1.85 | 7.34 | 1.89 | 7.16 | 1.93 | 6.80 | 2.00 |
+-----------------+------+------+------+------+------+------+------+------+
| **15  °C**      | 7.79 | 1.64 | 7.60 | 1.68 | 7.42 | 1.71 | 7.05 | 1.78 |
+-----------------+------+------+------+------+------+------+------+------+

The first step is to load the table into a pandas :class:`~pandas.DataFrame`.
This can be done for example by using the method ``build_heating_permap``.
Copy the table as formatted below in a file
named ``heating-performance-map.dat``. ::

    Tdbr 15.6 18.3 21.1 23.9
    Tdbo TC IP TC IP TC IP TC IP
    -26.1 3.62 2.15 3.54 2.19 3.45 2.23 3.28 2.31
    -20.6 4.63 2.16 4.52 2.20 4.41 2.24 4.19 2.32
    -15.0 5.11 2.17 4.99 2.21 4.86 2.25 4.62 2.34
    -10.0 5.36 2.13 5.23 2.18 5.10 2.22 4.85 2.30
    -5.0 5.86 2.10 5.72 2.14 5.58 2.18 5.30 2.26
    0.0 6.03 2.07 5.88 2.11 5.74 2.15 5.45 2.23
    5.0 6.58 1.88 6.43 1.92 6.27 1.96 5.96 2.04
    8.3 6.80 1.86 6.64 1.90 6.48 1.94 6.15 2.02
    10.0 7.52 1.85 7.34 1.89 7.16 1.93 6.80 2.00
    15.0 7.79 1.64 7.60 1.68 7.42 1.71 7.05 1.78


Then, you can load it using

.. ipython::

   In [1]: import fillomino

   In [2]: hpm = fillomino.build_heating_permap("heating-performance-map.dat")

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

Now let's say that
we want to add a (normalized) frequency input in the performance map.
For example, let's add entries ranging from 0.1, 0.2, ... up to 1.0:

.. ipython::

   In [4]: import numpy as np

   In [5]: hpm.pmf.entries['freq'] = np.arange(0.1, 1.1, 0.1)

   In [6]: hpm.pmf.entries['freq']
   Out[6]: array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1. ])

Before filling the performance map, we have to specify explicitly
the operating mode to use the appropriate performance correction.
By default, it is assumed that the above performance map is given
at the rated frequency.

.. ipython::

   In [7]: hpm.pmf.mode = 'heating'

Now we can fill it:

.. ipython::

   In [8]: hpm_full = hpm.pmf.fill()

   In [9]: hpm_full
   Out[9]:
   heating                     power  capacity
   Tdbr Tdbo  AFR     freq
   15.6 -26.1 0.00001 0.1   0.007630  0.017526
                      0.2   0.044690  0.102655
                      0.3   0.124994  0.287113
                      0.4   0.257420  0.591299
                      0.5   0.446897  1.026530
   ...                           ...       ...
   23.9  15.0 1.00000 0.6   0.574898  3.088145
                      0.7   0.825348  4.272689
                      0.8   1.115671  5.397201
                      0.9   1.437417  6.340601
                      1.0   1.780000  7.050000
   [800 rows x 2 columns]

.. note::
    Even though no air flow rate entries where specified,
    an air flow rate (AFR) column was also added with "dummy" values
    because it is required by the Type |_| 3254.

Before ending with writing the table to a file,
here's a tip for normalizing the performance map values.
Tables are usually provided in a non-normalized way, but the Type |_| 3254
works with normalized data. The table ``hpm_full`` can be normalized
by providing rated values in a DataFrame:

.. ipython::

   In [10]: import pandas as pd

   In [11]: rated_values = pd.DataFrame({'capacity': [4.69], 'power': [1.01]})

   In [12]: hpm_norm = hpm_full.pmf.normalize(values=rated_values)

   In [13]: hpm_norm.pmf.normalized
   Out[13]: True

   In [14]: hpm_norm
   Out[14]:
   heating                     power  capacity
   Tdbr Tdbo  AFR     freq
   15.6 -26.1 0.00001 0.1   0.007554  0.003737
                      0.2   0.044248  0.021888
                      0.3   0.123756  0.061218
                      0.4   0.254872  0.126077
                      0.5   0.442472  0.218876
   ...                           ...       ...
   23.9  15.0 1.00000 0.6   0.569206  0.658453
                      0.7   0.817176  0.911021
                      0.8   1.104625  1.150789
                      0.9   1.423185  1.351941
                      1.0   1.762376  1.503198
   [800 rows x 2 columns]

or directly through the ``fill`` method:

.. ipython::

   In [15]: hpm_norm = hpm.pmf.fill(norm=rated_values)


Normalization can only be performed once;
trying to normalize a second time will fail:

.. ipython::
   :okexcept:

   In [16]: hpm_norm.pmf.normalize(values=rated_values)

Finally, we can write the table to a file:

.. ipython::

   In [17]: hpm_norm.pmf.write("complete-heating-performance-map.dat")

That's it! You should now have a file named
``complete-heating-performance-map.dat``
that can directly be used with the Type |_| 3254.


.. _installation:

Installation
------------

You can install Fillomino
through `pip <https://pip.pypa.io/en/stable/>`_ by running::

    $ pip install fillomino

.. _Type 3254: https://github.com/polymtl-bee/vcaahp-model
