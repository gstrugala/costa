.. currentmodule:: costa.permap

.. define non-breaking space by |_|
.. |_| unicode:: 0xA0
   :trim:


Loading the performance map
===========================

Performance map objects (:class:`Permap`\ s) in Costa are represented as an extension of the
pandas :class:`~pandas.DataFrame` structure. They can therefore benefit from
a wide variety of methods to process and arrange the data.

For the :meth:`~Permap.fill` method to work properly,
the DataFrame representing the performance table must have a specific format.
There are two ways to obtain an adequate DataFrame.
One way is to format it yourself through Python scripting using pandas methods.
The other way is to format the performance file so that it can be correctly
interpreted by the :meth:`~costa.buildpermap.build_heating_permap` and
:meth:`~costa.buildpermap.build_cooling_permap` methods.
These methods will in turn translate the file into an adequate DataFrame.


Format the DataFrame
--------------------

The performance map DataFrame structure must obey the two following rules:

**Table inputs constitute the DataFrame index.**
   If there are multiple quantities involved (as it is usually the case),
   a :class:`~pandas.MultiIndex` must be used.
   (See `indexing with a MultiIndex`_ for more info.)
   Each level in the index must be named after the corresponding quantity,
   following the :ref:`index names convention <index convention>`.

**Table outputs constitute the DataFrame columns.**
   Each column correspond to a specific quantity, like the index levels.
   The columns values represent the performance (the output) values,
   and each column name represent the name of the associated output quantity
   (see :ref:`column names convention <column convention>`).

Consider for example a performance map with two input quantities: the room air
temperature :math:`T_{dbr}` and the outdoor air temperature :math:`T_{dbo}`.
Let's say that there are three entries for :math:`T_{dbr}` and four entries
for :math:`T_{dbo}`:

- :math:`T_{dbr}` entries: 18.3 |_| °C, 21.1 |_| °C and 23.9 |_| °C
- :math:`T_{dbo}` entries: –20.6 |_| °C, –10 |_| °C, 0 |_| °C and 15 |_| °C

The performance map DataFrame would thus have :math:`3 \times 4 = 12` rows
and look like this: ::

   heating     capacity  power
   Tdbr Tdbo
   18.3 -20.6      4.52   2.20
        -10.0      5.23   2.18
         0.0       5.88   2.11
         15.0      7.60   1.68
   21.1 -20.6      4.41   2.24
        -10.0      5.10   2.22
         0.0       5.74   2.15
         15.0      7.42   1.71
   23.9 -20.6      4.19   2.32
        -10.0      4.85   2.30
         0.0       5.45   2.23
         15.0      7.05   1.78

.. note::
   The order of the index levels and the columns doesn't matter,
   as long as their names follow the naming conventions.

|

.. _index convention:
.. table:: `Index names convention`
   :widths: auto

   ==========  ====================================
      Name                 Quantity
   ==========  ====================================
   ``'Tdbr'``  Room air dry-bulb temperature
   ``'Tdbo'``  Outdoor air dry-bulb temperature
   ``'Twbr'``  Room air wet-bulb temperature [#f1]_
   ``'AFR'``   Indoor unit air flow rate
   ``'freq'``  Compressor frequency
   ==========  ====================================

|

.. _column convention:
.. table:: `Column names convention`
   :widths: auto

   ==============  ====================================
        Name                     Quantity
   ==============  ====================================
   ``'power'``     Heat pump total power input
   ``'capacity'``  Heat pump capacity
   ``'COP'``       Heat pump coefficient of performance
   ==============  ====================================

|

Format the input file
---------------------

If you'd rather not use pandas to get an adequate DataFrame, there is a plan B:
you can use a tool of your choice to create a performance map file that can be
interpreted by the methods :meth:`~costa.buildpermap.build_<mode>_permap`
(see :ref:`quick tutorial <tuto>`).
However, as of now the diversity of acceptable file formats is pretty limited,
so this method offers less flexibility.
The required file formats for each operating mode
are described in the following sections.

Heating input file
~~~~~~~~~~~~~~~~~~
In heating mode, only files with indoor and outdoor dry-bulb temperatures
inputs are accepted—this is the most common format in manufacturer datasheets.
To work with the method :meth:`~costa.buildpermap.build_heating_permap`,
the performance table from the example above has to be formatted this way: ::

    Tdbr 18.3 21.1 23.9
    Tdbo TC IP TC IP TC IP
    -20.6 4.52 2.20 4.41 2.24 4.19 2.32
    -10.0 5.23 2.18 5.10 2.22 4.85 2.30
    0.0 5.88 2.11 5.74 2.15 5.45 2.23
    15.0 7.60 1.68 7.42 1.71 7.05 1.78

.. note::
   Only the numerical data (in red) actually matters, the labels are `not`
   interpreted. Thus if you format this way: ::

      Tdbo -20.6 -10.0 0.0 15.0
      Tdbr TC IP TC IP TC IP TC IP
      18.3 4.52 2.20 5.23 2.18 5.88 2.11 7.60 1.68
      21.1 4.41 2.24 5.10 2.22 5.74 2.15 7.42 1.71
      23.9 4.19 2.32 4.85 2.30 5.45 2.23 7.05 1.78

   the (room) temperatures 18.3 |_| °C, 21.1 |_| °C and 23.9 |_| °C will be
   interpreted as outdoor temperatures values. This also means that you can
   replace the cells in black with anything you want, since they are discarded.


Cooling input file
~~~~~~~~~~~~~~~~~~

The cooling mode file format is very similar to the one in heating mode,
with two notable exceptions: room air wet-bulb temperatures (:math:`T_{wbr}`)
are also provided, and there is an additional "sensible heat capacity" (SHC)
column. To work with the method :meth:`~costa.buildpermap.build_cooling_permap`,
the cooling performance table must be formatted in this way: ::

   Tdbr 21.1 26.7 32.2
   Twbr 15.6 19.4 22.8
   Tdbo TC SHC IP TC SHC IP TC SHC IP
   15.0 3.25 2.71 0.41 3.70 3.18 0.42 4.14 3.37 0.44
   25.0 3.49 2.89 0.63 3.97 3.41 0.64 4.44 3.61 0.65
   30.6 3.30 2.73 0.70 3.75 3.22 0.71 4.20 3.42 0.73
   40.0 2.62 2.29 0.72 2.97 2.70 0.74 3.33 2.87 0.75

Note that this format omit some dry-bulb / wet-bulb combinations
(e.g. there is no data for
:math:`T_{dbr} =` |_| 21.1 |_| °C and :math:`T_{wbr} =` |_| 19.4 |_| °C),
but this is how manufacturers usually provide cooling performance data. Since
Costa provides a way to determine the sensible heat ratio based on the
conditions (see :ref:`using default corrections <default corrections>`),
the SHC column is dropped by the method
:meth:`~costa.buildpermap.build_cooling_permap`.

.. rubric:: Footnotes

.. [#f1] The room air wet-bulb temperature should only be included in `cooling`
   performance maps, as it does not have any impact on performance in heating.


.. _indexing with a MultiIndex:
   https://pandas.pydata.org/pandas-docs/stable/user_guide/advanced.html
