"""
The :mod:`~costa.defaults` module provide default correction functions
used to obtain missing values in a performance map.
"""

import numpy as np


def weibull(x, amp, scale, shape):
    """Scaled `Weibull cumulative distribution function`_.

    .. _Weibull cumulative distribution function:
       https://en.wikipedia.org/wiki/Weibull_distribution#Cumulative_distribution_function
    """
    return amp * (1 - np.exp(-(x/scale) ** shape))


def compexp(x, amp, scale, shape, lift, shift):
    """Lifted and shifted version of the `compressed exponential function`_.

    .. _compressed exponential function:
       https://en.wikipedia.org/wiki/Stretched_exponential_function
    """
    shifted = np.maximum(x - shift, 0)  # avoids divergence at low values
    return (amp - lift) * np.exp(-(shifted / scale) ** shape) + lift


def default_correction(mode, pminput, pmoutput=None):
    """Return performance map output correction.

    Get a callable correction of a given output quantity depending on a
    certain input quantity in a specific operating mode.

    Parameters
    ----------
    mode : {'cooling', 'heating'}
        The operating mode corresponding to the desired correction.
    pminput : {'freq', 'AFR', 'Twbr', 'SHR'}
        The quantity which the desired correction should depend on.  The
        `'SHR'` option is only available in cooling mode.
    pmoutput : {'COP', 'power'}, optional
        The quantity to which the desired correction should apply.  Should
        not be specified when `pminput` is `'SHR'`.

    Returns
    -------
    correction : callable
        Correction for the specified quantities in the given mode.

    Examples
    --------
    >>> corr = default_correction('heating', 'freq', 'power')
    >>> corr(0)
    0.0
    >>> corr(0.8)
    0.6267813236509203
    >>> corr(1)
    0.9999997589861805

    """
    # Check and format arguments
    if 'cool' in mode.lower():
        mode = 'cooling'
    elif 'heat' in mode.lower():
        mode = 'heating'
    else:
        raise ValueError("'mode' must be either 'cooling' or 'heating'.")

    if pmoutput is None:
        if pminput.lower() != 'shr':
            raise ValueError(
                "'pmoutput' argument is mandatory when 'pminput' is not 'SHR'."
            )
    else:
        if 'cop' in pmoutput.lower():
            pmoutput = 'COP'
        elif 'power' in pmoutput.lower():
            pmoutput = 'power'
        else:
            raise ValueError("'pmoutput' must be either 'COP' or 'power'.")

    if 'freq' in pminput:
        # Choose the right parameters and function for the correction
        parameters = {
            ('cooling', 'COP'): (2.195, 0.5185, 2, 0.8884, 0.1868),
            ('cooling', 'power'): (
                1.5579754390604839, 0.9882406279903194, 2.238044893056409
            ),
            ('heating', 'COP'): (
                1.364250052, 0.56092853627625, 2, 0.616081, 0.5418215480886562
            ),
            ('heating', 'power'): (2.5121, 1.30389, 2.5551829)
        }[(mode, pmoutput)]
        function = weibull if pmoutput == 'power' else compexp
        return lambda x: function(x, *parameters)
    elif pminput == 'AFR':
        # Placeholder (no correction for now)
        def correction_afr(AFR): return 1
        return correction_afr
    elif pminput == 'Twbr':
        # Placeholder (no correction for now)
        def correction_wetbulb(Twbr): return 1
        return correction_wetbulb
    elif pminput.lower() == 'shr':
        if mode == 'heating':
            raise ValueError("SHR only available in cooling mode.")

        def shr(dT):
            return 1 + 0.6 * (np.tanh(0.144 * dT - 0.724) - 1)

        return shr
    else:
        error_msg = "'pminput' must be either 'freq', 'AFR', 'Twbr' or 'SHR'."
        raise ValueError(error_msg)


def build_default_corrections(mode):
    """Return a dict with all corrections for a certain operating mode.

    Parameters
    ----------
    mode : {'cooling', 'heating'}
        The operating mode corresponding to the desired corrections.

    Returns
    -------
    default_corrections : dict
        Corrections for the specified mode.

    """
    default_corrections = {
        pminput: {
            pmoutput: default_correction(mode, pminput, pmoutput)
            for pmoutput in ('COP', 'power')
        }
        for pminput in ('AFR', 'freq', 'Twbr')
    }

    if 'cool' in mode.lower():
        default_corrections['SHR'] = default_correction(mode, 'SHR')

    return default_corrections
