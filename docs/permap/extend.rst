.. currentmodule:: costa.permap

.. define non-breaking space by |_|
.. |_| unicode:: 0xA0
   :trim:

.. role:: py(code)
   :language: py
   :class: highlight


Extending the performance map
=============================

To complete the performance map, Costa relies on correction curves,
following the methodology described by [Strugala]_. Here's a TLDR:

   1. Select the performance map entries for each quantity to add.

   2. Multiply the original performance map by a correction factor that
      depends on the entry value, for each selected entry.

Thus before filling the performance map, new entries and the corrections to use
have to be specified, along with some other things.
The following sections explain how to do so, and the last one shows how to
finally fill the performance map.


Specify the operating mode
--------------------------

The corrections and the variables involved in the performance map depend on the
operating mode (heating or cooling), which must therefore be specified before
filling. (Not doing so will raise an exception.)

This can be done simply by assigning the string ``'heating'`` or ``'cooling'``
to the attribute :attr:`~Permap.mode`.

.. warning::
   When using :class:`Permap` attributes or methods,
   don't forget to use the ``pm`` prefix !


.. _set entries:

Set the performance map entries
-------------------------------

The entries are stored in the :attr:`~Permap.entries` attribute, in the form
of a :class:`dict` with input quantities as keys and entries as values.
Valid keys for referencing input quantities are found in the
:ref:`index names tables <index convention>`, and the selected entries must
be specified in the form of a :class:`list` or a NumPy :class:`~numpy.ndarray`.
For example, to set frequency entries 0.1, 0.5 and 0.9 for a performance map
``permap``, you would do

>>> permap.pm.entries['freq'] = [0.1, 0.5, 0.9]


Manage the correction functions
-------------------------------

Correction functions are the backbone of this performance map completion
methodology. Some :ref:`default corrections <default corrections>` are
available for you to use, but you can also
:ref:`use your own <custom corrections>`.
Correction functions are stored in a dictionary like the
:ref:`entries <set entries>`, in the :attr:`~Permap.corrections` attribute.
However since corrections depends both on the input and output quantities of the
performance map, the dictionary is more nested; it has the following form: ::

   {
      'AFR': {
         'power': <function>,
         'capacity': <function>,
         'COP': <function>,
      },
      'freq': {
         'power': <function>,
         'capacity': <function>,
         'COP': <function>,
      },
      ...
   }

For example, to get the power correction as a function of frequency,
you could use :py:`permap.pm.corrections['freq']['power']` (see examples in
the :class:`Permap` docstring). There is also a dedicated getter method,
:meth:`~Permap.get_correction`, that would return the same correction
with :py:`permap.pm.get_correction('freq', 'power')`.
It also allows to get all corrections associated with a specific input
by omitting the second argument.


.. _default corrections:

Use default corrections
~~~~~~~~~~~~~~~~~~~~~~~

Everything related to the default corrections is contained in the
:mod:`~costa.defaults` module.
For getting a specific correction, there is the function
:func:`~costa.defaults.default_correction`.
As with the :meth:`Permap.get_correction` method, it returns a callable
that can easily be visualized:

.. plot::
   :include-source:

   import numpy as np
   import matplotlib.pyplot as plt
   from costa.defaults import default_correction

   corr = default_correction('heating', 'freq', 'power')
   freq = np.linspace(0, 2, 100)
   plt.plot(freq, corr(freq))
   plt.xlabel("Normalized compressor frequency")
   plt.ylabel("Heat pump power correction")


You can also get all the corrections associated with a certain
:attr:`~Permap.mode` arranged in a :class:`dict` structure as shown above,
using the function :func:`~costa.defaults.build_default_corrections`.

.. note::
   As of today, there are no regressions for the air flow rate (``AFR``) or the
   indoor wet-bulb temperature (``Twbr``); all corrections associated with
   these quantities are equal to 1.


.. _custom corrections:

Add custom corrections
~~~~~~~~~~~~~~~~~~~~~~

Corrections can easily be edited or added through the
:attr:`~Permap.corrections` attribute, but you may want to use the
:meth:`~Permap.set_correction` method instead. Indeed, it performs some
security checks before updating the corrections dictionary, and it can also
return a new instance instead of modifying the performance table in-place
(see ``inplace`` argument.).

There is also the :meth:`~Permap.set_corrections` method, which allows you
to specify all corrections associated with an input quantity. In addition,
it automatically adds correction functions that can be deduced from the others.
Indeed, since the output quantities are not independent
(:math:`\text{COP} = \dot{Q} / P`) you can give only two corrections out of
the three and the last one will be automatically added.
For example, if you have a COP and a power correction named respectively
``cop`` and ``power``, you can do ::

   new_corrections = {'COP': cop, 'power': power}
   new_permap = permap.pm.set_corrections('freq', new_corrections)

and :py:`new_permap.pm.corrections['freq']` should have an entry ``'capacity'``.


Adjust the initial normalized values
------------------------------------

By normalizing everything w.r.t. rated values, the correction functions must
take the value 1 when the normalized input is 1 (i.e. for any correction
function :math:`\varphi`, :math:`\varphi(1) = 1`). But performance tables are
not always provided at rated values. For example, it may happen that a spec
sheet provide performance values at the maximum frequency :math:`f_\text{max}`,
while the rated frequency :math:`f_\text{r}` is only half of
:math:`f_\text{max}`. In that case, the normalized frequency
:math:`\nu = f / f_\text{r}` would range from 0 to 2, and the initial
performance data would be given at :math:`\nu = 2`.
Since :math:`\varphi(2) \neq 1`, one cannot just multiply the performance map
by :math:`\varphi(\nu)` to extend it; we have to make sure that values are
preserved at :math:`\nu = 2`. Thus, we must adjust the correction and instead
multiply by :math:`\varphi(\nu) / \varphi(2)`.

More generally, if the performance data is provided at a certain condition
:math:`v^*` different from the rated value :math:`v_\text{r}`, the correction
:math:`\varphi(v)` must be adjusted by dividing it by
:math:`\varphi(v^*/v_\text{r})`. Therefore the ratio :math:`v^*/v_\text{r}`,
called the `initial normalized value`, must be explicitly specified for each
normalized quantity to extend the performance map correctly. This can be done
using the attribute :attr:`~Permap.initial_norm_values`, where values are
once again stored in a dictionary whose keys are the normalized quantities
in question. So for example, if performance is provided at a frequency of
120 |_| Hz but the rated frequency is 75 |_| Hz, you would have to set

>>> permap.pm.initial_norm_values['freq'] = 120 / 75

.. note::
   By default, i.e. if you don't make any :class:`dict` assignment, all those
   values are set to |_| 1. This means that, **unless specified otherwise,
   it is assumed that initial performance data is provided at rated values**.


.. _fill pm:

Fill the performance map
------------------------

Once you have set the operating mode, the performance map entries, the
correction functions and the initial normalized values, you can
:meth:`~Permap.fill` the performance map. To do so, simply

>>> permap_full = permap.pm.fill()

Note that you can combine the :meth:`~Permap.fill` operation with the
:meth:`~Permap.normalize` operation (see :ref:`normalizing data <norm>`),
by providing rated values to the :meth:`~Permap.fill` method.



.. rubric:: References

.. [Strugala] Strugala, G. (2020). `Experimental testing and modelling of
   variable capacity air-to-air heat pumps`
   (Master's thesis, Polytechnique Montréal).
   Retrieved from https://publications.polymtl.ca/5285/
