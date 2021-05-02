.. currentmodule:: fillomino.permapfiller

.. define non-breaking space by |_|
.. |_| unicode:: 0xA0
   :trim:


Writing the performance map
===========================

Once the performance map is filled, it must be written to a file with a certain
format so that it can be interpreted by the Type |_| 3254.
Before that though, there is one last step: specify the operating ranges.

Ideally, the limits of the operating conditions of the heat pump should
correspond to the limits of the performance map, but it may happen that
the operating ranges are wider than the performance map domain. Hence those
limits must be given to the Type |_| 3254, and therefore be included in the
performance file. This can be easily done using the :attr:`~PermapFiller.ranges`
attribute. For example, if you want to specify an outdoor temperature range
that goes from –30 °C to 15 °C, you should do

>>> permap.pmf.ranges['Tdbo'] = [-30, 15]

Note that for each input quantity where no operating range is explicitly given,
the performance map limits are used.

Finally, to write the performance map to ``path/filename.dat``, just

>>> permap.pmf.write("path/filename.dat")

and you're done !
