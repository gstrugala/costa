"""
The ``permap`` module provides the Permap class, an extension of
:class:`pandas.DataFrame` to fill incomplete performance maps.
"""

import warnings
from copy import deepcopy
from collections.abc import MutableMapping

import numpy as np
import pandas as pd

from .defaults import build_default_corrections


@pd.api.extensions.register_dataframe_accessor('pm')
class Permap:
    """
    Complete missing values in a performance map.

    Permap objects are accessible through the `DataFrame accessor`_ ``pm``.
    They provide a handful of methods to help extend an initially incomplete
    performance map, given as a :class:`~pandas.DataFrame`.

    Parameters
    ----------
    pandas_obj : :class:`pandas.DataFrame`
        The DataFrame representing the performance map.

    Attributes
    ----------
    mode : {'heating', 'cooling'}, default None
        The operating mode associated with the performance data.
    normalized : bool, default False.
        ``True`` if the performance data is normalized.
        It is automatically set to ``True`` after using the
        :meth:`normalize` method.
    entries : dict, default {'freq': [0.2, 0.5, 1], 'AFR': [0, 1]}
        Entries for the missing quantities in the performance map.
        Particular entries can be set using
        ``self.entries[quantity] = list_of_entries``
    corrections : dict, default None
        Two-levels nested dictionary  with single variable correction functions
        used to extend the performance map.  A different correction
        should be provided for each input and output quantity.  The keys
        of the first level are the input quantities and those of the
        second level are the output quantities.  Dictionary values
        (the corrections) must be provided as functions with one
        argument. See examples for more details.
    initial_norm_values : :class:`dict`, default :obj:`None`
        Manufacturer tables are not always provided in rated conditions;
        for example, some performance tables are provided at maximum
        compressor frequency and not at the rated frequency value.  For
        each normalized input quantity that is not in the initial performance
        table, this attributes specifies the value corresponding to the initial
        data, normalized by the actual rated value. If none have been set,
        the default dict ``{'freq': 1, 'AFR': 1}`` is assigned when the
        operating mode is set.
    ranges : dict
        Operating ranges for the input quantities of the performance map.
        The limits of the performance map are used for the default ranges.
    restricted_levels : dict
        Each key corresponds to a level name of the performance map.
        The associated value is either ``None``, ``'left'``, ``'right'`` or
        ``'both'``, i.e. the side(s) where the level has already been
        restricted.

    Examples
    --------
    Build an incomplete performance map and
    set (missing) normalized frequency entries:

    >>> hm = costa.build_heating_permap()
    >>> hm.pm.entries['freq'] = np.arange(0.1, 2.1, 0.1)

    There are no corrections or manufacturer values factors by default
    until the operating mode is set:

    >>> hm.pm.corrections is None and hm.pm.initial_norm_values is None
    True
    >>> hm.pm.mode = 'heating'
    >>> hm.pm.initial_norm_values
    {'freq': 1, 'AFR': 1}
    >>> corr = hm.pm.corrections['freq']['power']
    >>> corr(0.5)
    0.20785906320354824
    >>> corr(1)
    0.9999997589861805

    If performances are not given at rated frequency, a correction
    factor must be set.  Assuming performances are given at maximum
    frequency (120 Hz) and rated frequency is 60 Hz, the frequency
    correction ratio should be

    >>> hm.pm.initial_norm_values['freq'] = 120 / 60

    This value will affect the output of the method :meth:`correct`,
    and thus also :meth:`extend` and :meth:`fill`.

    .. _DataFrame accessor: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.api.extensions.register_dataframe_accessor.html

    """

    _attributes_to_copy = (
        '_mode',
        '_normalized',
        '_entries',
        '_corrections',
        '_initial_norm_values',
        '_ranges',
        '_restricted_levels'
    )

    def __init__(self, pandas_obj):
        """Constructor for the Permap class."""
        self._obj = pandas_obj
        self._mode = None
        self._normalized = False
        self._entries = {'freq': [0.2, 0.5, 1], 'AFR': [1e-5, 1]}
        self._corrections = None
        self._initial_norm_values = None
        self._ranges = ADict(
            self.index_ranges(pandas_obj.index),
            pm=self,
            setitem=set_range
        )
        self._restricted_levels = {key: None for key in self.ranges}

    def update_data(self, df, update_ranges=True, keep_restrictions=False):
        """Return a new performance map with updated data.

        Parameters
        ----------
        df : :class:`~pandas.DataFrame`
            The updated data.
        update_ranges : bool, default True
            If ``False``, the original operating ranges will be kept.
        keep_restrictions : bool, default False
            If ``True``, any level already restricted will keep the same
            restriction ('left', 'right' or 'both').

        Returns
        -------
        :class:`~pandas.DataFrame`
            Data in df with attributes ranges and restricted_levels
            adjusted accordingly from the index of `df`.

        """
        pm = df.pm.copyattr(self)
        if update_ranges:
            pm.pm._ranges = ADict(
                self.index_ranges(df.index),
                pm=pm.pm,
                setitem=set_range
            )
        pm.pm._restricted_levels = {key: None for key in pm.pm.ranges}
        if keep_restrictions:
            for key, restriction in self.restricted_levels.items():
                if restriction is not None and key in pm.pm.ranges:
                    pm.pm._restricted_levels[key] = restriction
        return pm

    @property
    def data(self):
        return self._obj

    @property
    def ranges(self):
        return self._ranges

    @ranges.setter
    def ranges(self, new_ranges):
        """Setter for the `ranges` property."""
        if any(key not in self.data.index.names for key in new_ranges.keys()):
            raise ValueError("range keys must be in table level names.")
        if isinstance(new_ranges, ADict):
            self._ranges = new_ranges
        elif isinstance(new_ranges, dict):
            self._ranges = ADict(new_ranges, pm=self, setitem=set_range)
        else:
            raise TypeError("'ranges' attribute must be a dict.")

    @classmethod
    def index_range(cls, index, level):
        """Return the range of a pandas MultiIndex along a given level.

        Parameters
        ----------
        index : pandas MultiIndex
            The index must have ``min`` and ``max`` methods.
        level
            The name of the level for which the range must be returned.

        Returns
        -------
        pandas Interval
            range of the index along the specified level,
            in the form (lower bound, upper bound).

        """
        index_values = index.get_level_values(level)
        return pd.Interval(
            index_values.min(),
            index_values.max(),
            closed='both'
        )

    @classmethod
    def index_ranges(cls, index):
        """Get ranges for each level of a pandas MultiIndex as a dict."""
        return {level: cls.index_range(index, level) for level in index.names}

    @property
    def mode(self):
        # """The operating mode corresponding to the performance data."""
        return self._mode

    @mode.setter
    def mode(self, operating_mode):
        """Setter for the operating mode.

        If either the corrections or the manufacturer values factors are
        None, default values are automatically set together with the
        mode.

        Parameters
        ----------
        operating_mode : {'heating', 'cooling'}
            The operating mode associated with the performance data.

        Warns
        -----
        UserWarning
            If corrections are not None and a new mode is set
            (corrections are not overwritten).

        """
        if 'cool' in operating_mode.lower():
            self._mode = 'cooling'
        elif 'heat' in operating_mode.lower():
            self._mode = 'heating'
        else:
            err_msg = "'value' argument must be either 'heating' or 'cooling'."
            raise ValueError(err_msg)
        self._obj.columns.name = self.mode
        if self.corrections is None:
            self.corrections = build_default_corrections(self.mode)
            self._add_corrections(inplace=True)
        else:
            warnings.warn(
                "Corrections are already set and were not overwritten, though "
                "they may need to be changed after setting a new mode."
            )
        if self.initial_norm_values is None:
            self.initial_norm_values = {'freq': 1, 'AFR': 1}
            if self.mode == 'cooling':
                self.initial_norm_values['Twbr'] = 1

    @property
    def normalized(self):
        return self._normalized

    @property
    def restricted_levels(self):
        return self._restricted_levels

    def copy(self):
        return self.copyattr(self)

    def copyattr(self, other):
        """Return a copy of the Permap with some selected attributes
        copied from `other`.
        """
        new = self.data.copy(deep=True)
        if isinstance(other, Permap) or hasattr(other, 'pm'):
            pm = other.pm if hasattr(other, 'pm') else other
            for attribute in self._attributes_to_copy:
                setattr(new.pm, attribute, deepcopy(getattr(pm, attribute)))
        else:
            first = type(other).__name__[0].lower()
            aan = 'a' if first in ('a', 'e', 'i', 'o', 'u') else 'an'
            raise TypeError(
                f"argument should be a {type(self).__name__}. "
                f"You provided {aan} {type(other).__name__}."
            )
        return new

    @property
    def entries(self):
        return self._entries

    @entries.setter
    def entries(self, new_entries):
        # Particular entries can be set using self.entries[quantity] = entries
        #                                             |        |          |
        #                                           dict      str        list
        self._entries = new_entries

    def normalize(self, values=None):
        """Normalize values in the performance map.

        Parameters
        ----------
        values : :class:`~pandas.DataFrame`, optional
            A DataFrame with one row containing the rated values
            of the performance map output quantities in its columns.
            The performance data will be normalized by those values.  By
            default, `values` is ``None`` and in that case the original
            performance map is returned.

        Returns
        -------
        pm : :class:`~pandas.DataFrame`
            A copy of the original performance map with performance
            values normalized according to the rated values, and the
            :attr:`normalized` attribute set to ``True``.

        Raises
        ------
        RuntimeError
            If the data is already normalized
            (:attr:`normalized` is ``True``).
        ValueError
            If there is an inconsistency between the Permap column
            index and the rated values DataFrame column index.

        See also
        --------
        fill :
            Fill the missing values and optionally normalize the data
            in one go.

        Examples
        --------
        >>> cm = costa.build_cooling_permap()
        >>> cm.pm.entries['freq'] =  np.arange(0.1, 1.5, 0.1)
        >>> cm.pm.mode = 'cooling'
        >>> cm
        cooling          capacity  power
        Tdbr Twbr Tdbo
        17.8 12.2 -10.0      3.03   0.28
                  -5.0       3.01   0.33
                   0.0       2.98   0.36
                   5.0       2.96   0.39
                   10.0      2.94   0.40
        ...                   ...    ...
        32.2 22.8  25.0      4.44   0.65
                   30.6      4.20   0.73
                   35.0      3.94   0.81
                   40.0      3.33   0.75
                   46.0      3.07   0.75
        [72 rows x 2 columns]

        >>> rated_values = pd.DataFrame({'capacity': [3.52], 'power': [0.79]})
        >>> cm_norm = cm.pm.normalize(rated_values)
        >>> cm_norm
        cooling          capacity     power
        Tdbr Twbr Tdbo
        17.8 12.2 -10.0  0.860795  0.354430
                  -5.0   0.855114  0.417722
                   0.0   0.846591  0.455696
                   5.0   0.840909  0.493671
                   10.0  0.835227  0.506329
                           ...       ...
        32.2 22.8  25.0  1.261364  0.822785
                   30.6  1.193182  0.924051
                   35.0  1.119318  1.025316
                   40.0  0.946023  0.949367
                   46.0  0.872159  0.949367
        [72 rows x 2 columns]

        Trying to normalize again will fail:

        >>> cm_norm.pm.normalize(rated_values)
        Traceback (most recent call last):
        ...
        RuntimeError: values are already normalized.

        """
        if self.normalized:
            raise RuntimeError("values are already normalized.")
        self._check_mode(before='normalizing')
        pm = self.copy()
        if values is None:
            return pm
        pmcols, vacols = set(pm.pm.data.columns), set(values.columns)
        mismatch = pmcols ^ vacols
        if mismatch < {'capacity', 'power', 'COP'}:
            if len(pmcols) > len(vacols):
                values = pm.pm._add_missing_df_column(values)
            elif len(pmcols) < len(vacols):
                pm.pm.data = pm.pm._add_missing_df_column(pm.pm.data)
            for quantity, value in values.iteritems():
                pm[quantity] /= value[0]
            pm.pm._normalized = True
            return pm
        else:
            raise ValueError(
                "DataFrame column index must match values column index."
                f"\nIndex are {list(pmcols)}"
                f" and {list(vacols)}"
            )

    @property
    def corrections(self):
        return self._corrections

    @corrections.setter
    def corrections(self, new_corrections):
        self._corrections = new_corrections

    @corrections.deleter
    def corrections(self):
        del self._corrections

    def get_correction(self, input_quantity, output_quantity=None):
        """Retrieve some specific correction functions.

        Parameters
        ----------
        input_quantity : str
            The input of the performance table, wich is the argument of the
            correction function to retrieve.
        output_quantity : str, optional
            The output of the performance table to which the returned
            correction apply.  By default, corrections for all outputs are
            returned in the form of a dictionary.

        Returns
        -------
        callable or dict
            The correction function used to correct the value of the output
            quantity depending on the value of the input quantity, if the
            output quantity is specified.  Otherwise, the correction
            function for each output quantity assembled in a dictionary.

        Raises
        ------
        RuntimeError
            If the operating :attr:`mode` is not yet set.

        See Also
        --------
        corrections : get all corrections as a dictionary.
        set_correction :
            Equivalent of :meth:`get_correction` for setting a
            single correction.
        set_corrections :
            Equivalent of :meth:`get_correction` for setting
            multiple corrections for a specific input quantity.

        """
        self._check_mode("getting correction")

        if output_quantity is None:
            return self._corrections[input_quantity]
        else:
            return self._corrections[input_quantity][output_quantity]

    def set_correction(
        self,
        input_quantity,
        output_quantity,
        new_correction,
        inplace=False
    ):
        """Set a correction function to adjust the value of a specific
        output quantity depending on a specific input quantity.

        Parameters
        ----------
        input_quantity : str
            The input of the performance table, wich is the argument of the
            correction function to set.
        output_quantity : str
            The output of the performance table to which the correction
            apply.
        new_correction : callable
            The new correction to be set.
        inplace : :class:`bool`, default ``False``
             If ``True``, performs operation in-place and returns ``None``.


        Returns
        -------
        :class:`~pandas.DataFrame` or :obj:`None`
            If `inplace` is ``False``, a copy of the DataFrame with the new
            correction is returned.

        Raises
        ------
        RuntimeError
            If the operating :attr:`mode` is not yet set.

        See Also
        --------
        corrections : get all corrections as a dictionary.
        get_correction :
            Equivalent of :meth:`set_correction` for getting
            specific corrections.
        set_corrections :
            Equivalent of :meth:`set_correction` for setting
            multiple corrections for a specific input quantity.

        """
        self._check_mode(before="setting new correction")
        new = None if inplace else self.copy()
        pm = self if inplace else new.pm
        updated_corrections = pm.corrections
        updated_corrections[input_quantity][output_quantity] = new_correction
        pm.corrections = updated_corrections
        return new

    def set_corrections(self, input_quantity, new_corrections):
        """Set a correction functions to adjust the value of all output
        quantities depending on a specific input quantity.

        Parameters
        ----------
        input_quantity : str
            The input of the performance table, wich is the argument of the
            correction functions to set.
        new_corrections : dict of callables
            The new corrections to be set, with keys corresponding to
            output quantities names.

        Returns
        -------
        :class:`~pandas.DataFrame`
            A copy of the DataFrame with the new corrections is returned.

        Raises
        ------
        RuntimeError
            If the operating :attr:`mode` is not yet set.

        See Also
        --------
        corrections : get all corrections as a dictionary.
        get_correction :
            Equivalent of :meth:`set_corrections` for getting
            specific corrections.
        set_correction :
            Equivalent of :meth:`set_corrections` for setting a
            single correction.

        """
        self._check_mode(before="setting new corrections")
        new = self.copy()
        updated_corrections = new.pm.corrections
        updated_corrections[input_quantity] = new_corrections
        new.pm.corrections = updated_corrections
        return new.pm._add_correction(input_quantity)

    @property
    def initial_norm_values(self):
        return self._initial_norm_values

    @initial_norm_values.setter
    def initial_norm_values(self, new_values):
        self._initial_norm_values = new_values

    @initial_norm_values.deleter
    def initial_norm_values(self):
        del self._initial_norm_values

    def _check_mode(self, before="doing what you did"):
        """Ensure that the mode is set."""
        if self.mode is None:
            error_message = f"attribute 'mode' must be set before {before}."
            raise RuntimeError(error_message)

    def _check_columns(self, keys):
        """Check coherence between column index and a set of keys."""
        columns, keys = set(self.data.columns), set(keys)
        if columns != keys:
            unmatched_cols = tuple(columns - keys)
            unmatched_keys = tuple(keys - columns)
            error_msg = ["DataFrame column index must match corrections keys."]
            if unmatched_cols != tuple():
                multiple = len(unmatched_cols) > 1
                faulty_cols = unmatched_cols[0] if multiple else unmatched_cols
                error_msg.append(
                    f"DataFrame columns not in correction keys: {faulty_cols}"
                )
            if unmatched_keys != tuple():
                multiple = len(unmatched_cols) > 1
                faulty_keys = unmatched_keys[0] if multiple else unmatched_keys
                error_msg.append(
                    f"Correction keys not in DataFrame columns: {faulty_keys}"
                )
            raise ValueError('\n'.join(error_msg))

    def _check_corrections(self, quantity):
        """Check that the number of corrections makes sense."""
        self._check_mode(before="checking for corrections")
        corrections_number = len(self.corrections[quantity])
        if corrections_number < 2:
            raise ValueError("there should be at least two corrections.")
        elif corrections_number > 3:
            raise ValueError("there are too many (or redundant) corrections.")

    def _add_correction(self, quantity, inplace=False):
        """Add an additional (redundant) correction.

        If a regression on another output quantity (e.g. COP instead of
        capacity) is preferable, this function can automatically add any
        missing correction function that can be deduced from the already
        existing ones.

        Parameters
        ----------
        quantity : str
            The input quantity whose values are used to compute the
            corrections.
        inplace : bool, default ``False``
            If ``True``, performs operation in-place and returns ``None``.

        Returns
        -------
        :class:`~pandas.DataFrame`
            A copy of the original DataFrame with additional regression(s).

        Raises
        ------
        RuntimeError
            If the operating :attr:`mode` is not yet set.

        See Also
        --------
        _add_corrections :
            Equivalent of :meth:`_add_correction` for adding
            regressions for all input quantities.
        set_correction : set a single correction.
        set_corrections :
            Set multiple corrections for a specific input quantity.

        """
        self._check_corrections(quantity)
        corrections = self.corrections[quantity]
        all_keys, keys = {'power', 'capacity', 'COP'}, set(corrections.keys())
        if all_keys == keys:
            return self.copy()
        missing_key = (all_keys - keys).pop()
        if missing_key == 'power':
            cap, COP = (corrections[qt] for qt in ('capacity', 'COP'))
            def new_correction(x): return cap(x) / COP(x)
        elif missing_key == 'capacity':
            power, COP = (corrections[qt] for qt in ('power', 'COP'))
            def new_correction(x): return power(x) * COP(x)
        elif missing_key == 'COP':
            power, cap = (corrections[qt] for qt in ('power', 'capacity'))
            def new_correction(x): return cap(x) / power(x)
        else:
            err_msg = "correction key should be 'capacity', 'power' or 'COP'."
            raise ValueError(err_msg)
        if inplace:
            self.set_correction(
                quantity, missing_key, new_correction, inplace=True)
        else:
            return self.set_correction(quantity, missing_key, new_correction)

    def _add_corrections(self, inplace=False):
        """See :meth:`_add_correction`."""
        new = None if inplace else self.copy()
        for quantity in set(self.corrections) - {'SHR'}:
            if inplace:
                self._add_correction(quantity, inplace=True)
            else:
                new.pm = new.pm._add_correction(quantity)
        if not inplace:
            return new

    @classmethod
    def _add_missing_df_column(cls, df):
        """Add an additional (redundant) output quantity column.

        Parameters
        ----------
        df : :class:`~pandas.DataFrame`

        Returns
        -------
        :class:`~pandas.DataFrame`
            A copy of the original DataFrame with additional column(s).

        """
        _df = df.copy()
        all_columns = {'capacity', 'power', 'COP'}
        columns = set(_df.columns)
        if columns == all_columns:
            return _df
        missing_column = (all_columns - columns).pop()
        if missing_column == 'power':
            missing_values = _df.capacity / _df.COP
        elif missing_column == 'capacity':
            missing_values = _df.power * _df.COP
        elif missing_column == 'COP':
            missing_values = _df.capacity / _df.power
        else:
            err_msg = "column names should be 'capacity', 'power' or 'COP'."
            raise ValueError(err_msg)
        _df[missing_column] = missing_values
        return _df

    def _add_missing_column(self):
        """See classmethod :meth:`_add_missing_df_column`."""
        return self.update_data(
            self._add_missing_df_column(self.data),
            keep_restrictions=True
        )

    def correct(self, corrections, entry, initial=1):
        """Apply corrections to ouput quantities.

        Parameters
        ----------
        corrections : dict
            A dict with output quantities to adjust as keys, and
            correction functions as values.
        entry : int or float
            Value of the input quantity for which corrections are to
            be applied.
        initial : int or float, default 1
            Initial normalized value
            (see attribute :attr:`initial_norm_values`).

        Returns
        -------
        :class:`~pandas.DataFrame`
            A corrected copy of the original DataFrame.

        Raises
        ------
        RuntimeError
            If there is an incoherence between the column index and the
            :attr:`corrections` keys
            (the ouput quantities to be corrected).

        See Also
        --------
        extend : extend performance map using corrections.
        fill : fill missing values in performance map.

        """
        self._check_columns(corrections.keys())
        new = self.copy()
        for quantity, correction in corrections.items():
            new[quantity] *= correction(entry) / correction(initial)
        return new

    def extend(self, corrections, entries, name='new dim'):
        """Extend the performance map along a new dimension.

        Parameters
        ----------
        corrections : dict
            A dict with output quantities to adjust as keys, and
            correction functions as values.
        entries : iterable of int or float
            Values of the input quantity for which corrections are to
            be applied.
        name : str, default 'new dim'
            Name of the quantity corresponding to the new dimension.

        Returns
        -------
        :class:`~pandas.DataFrame`
            An extended copy of the original DataFrame.

        Raises
        ------
        RuntimeError
            If there is an incoherence between the column index and the
            :attr:`corrections` keys (the ouput quantities to be corrected).

        See Also
        --------
        correct : apply corrections to ouput quantities.
        fill : fill missing values in performance map.

        """
        self._check_columns(corrections.keys())
        initial = self.initial_norm_values[name]
        new = pd.concat(
            [self.correct(corrections, entry, initial) for entry in entries],
            keys=entries,
            names=[name]
        )
        return self.update_data(new, keep_restrictions=True)

    def fill(self, norm=None):
        """Extend the performance to include frequency, air flow rate and
        (in cooling mode) wet-bulb temperature entries.

        Parameters
        ----------
        norm : :class:`~pandas.DataFrame`, optional
            DataFrame with the rated values used for normalizing the
            data (see `values` argument in the :meth:`normalize` method
            documentation). If not provided, the data is not normalized.

        Returns
        -------
        :class:`~pandas.DataFrame`
            An extended copy of the original DataFrame.

        Raises
        ------
        RuntimeError
            If there is an incoherence between the column index and the
            :attr:`corrections` keys
            (the ouput quantities to be corrected).
        RuntimeError
            If the data is already normalized
            (:attr:`normalized` is ``True``).
        RuntimeError
            If the operating :attr:`mode` is not yet set.

        See Also
        --------
        correct : apply corrections to ouput quantities.
        extend : extend performance map using corrections.
        write : write performance map to file.

        Examples
        --------
        Build cooling performance map and set the missing frequency entries

        >>> cm = costa.build_cooling_permap()
        >>> cm.pm.mode = 'cooling'
        >>> cm.pm.entries['freq'] =  np.arange(0.1, 1.5, 0.1)
        >>> cm
        cooling          capacity  power
        Tdbr Twbr Tdbo
        17.8 12.2 -10.0      3.03   0.28
                  -5.0       3.01   0.33
                   0.0       2.98   0.36
                   5.0       2.96   0.39
                   10.0      2.94   0.40
        ...                   ...    ...
        32.2 22.8  25.0      4.44   0.65
                   30.6      4.20   0.73
                   35.0      3.94   0.81
                   40.0      3.33   0.75
                   46.0      3.07   0.75
        [72 rows x 2 columns]

        Fill values for frequency ('freq'), wet-bulb room temperature
        ('Twbr') and air flow rate ('AFR'), and normalize data:

        >>> rated_values = pd.DataFrame({'capacity': [3.52], 'power': [0.79]})
        >>> cm.pm.fill(norm=rated_values)
        cooling                          power  sensible_capacity  latent_capacity
        Tdbr Twbr Tdbo  AFR     freq
        17.8 12.2 -10.0 0.00001 0.1   0.003268           0.010849         0.013296
                                0.2   0.015247           0.050620         0.062037
                                0.3   0.037015           0.122602         0.150254
                                0.4   0.068330           0.206249         0.252767
                                0.5   0.108010           0.264530         0.324193
                                        ...                ...              ...
        32.2 22.8  46.0 1.00000 0.9   0.821848           0.571090         0.206256
                                1.0   0.949367           0.640746         0.231413
                                1.1   1.064119           0.712520         0.257335
                                1.2   1.163336           0.777625         0.280849
                                1.3   1.245864           0.832545         0.300684
        [11232 rows x 3 columns]

        """
        self._check_mode("filling the performance map")
        if norm is not None and self.normalized:
            raise RuntimeError("values are already normalized")

        freq_corr = self.get_correction('freq')
        with_freq = self._add_missing_column().pm.extend(
            freq_corr, self.entries['freq'], name='freq'
        )
        AFR_corr = self.get_correction('AFR')
        with_AFR = with_freq.pm.extend(
            AFR_corr, self.entries['AFR'], name='AFR'
        )
        if self.mode == 'heating':
            new_level_order = ['Tdbr', 'Tdbo', 'AFR', 'freq']
            pm_norm = (
                with_AFR.reorder_levels(new_level_order).sort_index()
                .pm.copyattr(with_AFR).pm.normalize(norm)
            )
            permap = pm_norm.reindex(['power', 'capacity'], axis='columns')
        elif self.mode == 'cooling':
            without_Twbr = with_AFR.droplevel('Twbr').pm.copyattr(with_AFR)
            Twbr = with_AFR.index.get_level_values('Twbr').unique().to_numpy()
            Twbr_corr = self.get_correction('Twbr')
            with_Twbr = without_Twbr.pm.extend(Twbr_corr, Twbr, name='Twbr')
            pm_norm = with_Twbr.pm.normalize(norm)
            Tdb = pm_norm.index.get_level_values('Tdbr').to_numpy()
            Twb = pm_norm.index.get_level_values('Twbr').to_numpy()
            invalid_states = Tdb < Twb
            valid_states = np.logical_not(invalid_states)
            wb_depression = Tdb[valid_states] - Twb[valid_states]
            SHR = self.get_correction('SHR')
            pm_norm.loc[valid_states, 'sensible_capacity'] = (
                pm_norm.capacity.iloc[valid_states] * SHR(wb_depression)
            )
            pm_norm.loc[valid_states, 'latent_capacity'] = (
                pm_norm.capacity.iloc[valid_states]
                - pm_norm.sensible_capacity.iloc[valid_states]
            )
            # Put -999 flag at invalid states
            pm_norm.iloc[invalid_states, :] = -999
            new_level_order = ['Tdbr', 'Twbr', 'Tdbo', 'AFR', 'freq']
            new_index_order = ['power', 'sensible_capacity', 'latent_capacity']
            permap = (
                pm_norm.drop('capacity', axis='columns')
                .reorder_levels(new_level_order)
                .sort_index()
                .reindex(new_index_order, axis='columns')
            )
        else:
            raise ValueError("mode must either be heating or cooling")
        return permap.pm.copyattr(pm_norm)

    def write(self, filename, majororder='row'):
        """Write performance map to a file using a format compatible with
        the TRNSYS `Type 3254 <https://github.com/polymtl-bee/vcaahp-model>`_.

        Parameters
        ----------
        filename : str
            The name of the file to be written to.
        majororder : {'row', 'col'}
            Choose to write the performance map either in
            `row- or column-major order
            <https://en.wikipedia.org/wiki/Row-_and_column-major_order>`_.

        """
        if not isinstance(majororder, str):
            raise TypeError("order must be either 'row' or 'col'.")
        else:
            order = majororder.lower()
        if order not in ('row', 'col'):
            raise TypeError("order must be either 'row' or 'col'.")

        permap_formatted = pd.concat([self.data], keys=[''], names=['!#'])
        if order == 'col':
            levels = permap_formatted.index.names
            flip_levels = [levels[0]] + levels[-1:0:-1]
            permap_formatted = permap_formatted.reorder_levels(flip_levels)
        permap_formatted.sort_index().round(10).to_csv(filename, sep='\t')

        def prepend_line(line):
            with open(filename, 'r+') as f:
                content = f.read()
                f.seek(0, 0)
                f.write(line.rstrip('\r\n') + '\n' + content)

        def fetch_index(i):
            index = self.data.index.get_level_values(i).unique()
            return index.name, index.values

        prepend_line("!#\n!# Performance map\n!#")
        nlevels = self.data.index.nlevels
        for name, values in (fetch_index(i) for i in range(nlevels-1, -1, -1)):
            values_str = '\t'.join(str(v) for v in values)
            prepend_line(f"!# {name} values\n   {values_str}\n")
        for name, values in (fetch_index(i) for i in range(nlevels-1, -1, -1)):
            rng = self.ranges[name]
            prepend_line(f"   {len(values)}\t{rng.left}\t{rng.right}\n")
            s = f"!# Number of {name} data points, lower bound, upper bound\n"
            prepend_line(s)

        warning = (
            "!# This is a data file for Type 3254. Do not change the format.\n"
            "!# In PARTICULAR, LINES STARTING WITH !# MUST BE LEFT "
            "IN THE FILE AT THEIR LOCATION.\n"
            '!# Comments within "normal lines" (not starting with !#) '
            "are optional but the data must be there.\n"
            "!#\n!# Independent variables\n!#"
        )

        prepend_line(warning)


class ADict(MutableMapping):
    """A dictionary with customizable __setitem__ method."""

    def __init__(self, *args, pm=None, setitem=None, **kwargs):
        self.store = dict()
        self._pm = pm
        self._setitem = setitem
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        if self._setitem is None:
            self.store[key] = value
        else:
            self._setitem(self, self._pm, key, value)

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __repr__(self):
        return self.store.__repr__()


def set_range(self, pm, key, value):
    if pm is None:
        raise TypeError("'pm' cannot be None.")
    if key not in pm.data.index.names:
        raise ValueError("range keys must be in table level names.")
    if isinstance(value, pd.Interval):
        # Ensure that the interval is closed
        self.store[key] = pd.Interval(value.left, value.right, closed='both')
    else:
        try:
            self.store[key] = pd.Interval(*value, closed='both')
        except TypeError:
            raise TypeError(
                "The instance set must be an iterable with the range bounds,\n"
                "or a 'pandas.Interval' object."
            )
    # Check interval validity
    def minmax(array): return array.min(), array.max()
    pmmin, pmmax = minmax(pm.data.index.get_level_values(key))
    interval = self.store[key]
    if pmmin < interval.left or pmmax > interval.right:
        raise RuntimeError(
            "Interval must be larger than or equal to performance map limits."
        )
