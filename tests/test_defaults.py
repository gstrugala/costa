from collections import namedtuple

import pytest
import numpy as np
from numpy.testing import assert_almost_equal

from costa.defaults import default_correction


Quantity = namedtuple('Quantity', ['name', 'value'])


@pytest.mark.parametrize(
    "pminput, pmoutput",
    [
        (Quantity('freq', 0), Quantity('COP', 2.195)),
        (Quantity('freq', 0), Quantity('power', 0)),
        (Quantity('freq', 0.7), Quantity('COP', 1.3789477993991555)),
        (Quantity('freq', 0.7), Quantity('power', 0.5766019727968901)),
        (Quantity('freq', 1), Quantity('COP', 1.0000532657573047)),
        (Quantity('freq', 1), Quantity('power', 1)),
        (Quantity('AFR', 0.5), Quantity('power', 1)),
        (Quantity('Twbr', 18), Quantity('power', 1)),
        (Quantity('SHR', 0), Quantity(None, 0.028371470570884405)),
        (Quantity('SHR', 1), Quantity(None, 0.08640074218850757)),
        (Quantity('SHR', 10), Quantity(None, 0.7686552972040149)),
    ]
)
def test_cooling_corrections_values(pminput, pmoutput):
    corr = default_correction('cooling', pminput.name, pmoutput.name)
    assert_almost_equal(corr(pminput.value), pmoutput.value)


@pytest.mark.parametrize(
    "pminput, pmoutput",
    [
        (Quantity('freq', 0), Quantity('COP', 1.364250052)),
        (Quantity('freq', 0), Quantity('power', 0)),
        (Quantity('freq', 0.7), Quantity('COP', 1.3070592669355836)),
        (Quantity('freq', 0.7), Quantity('power', 0.4636782893546832)),
        (Quantity('freq', 1), Quantity('COP', 1.0000000415933386)),
        (Quantity('freq', 1), Quantity('power', 0.9999997589861805)),
        (Quantity('AFR', 0.5), Quantity('power', 1))
    ]
)
def test_heating_corrections_values(pminput, pmoutput):
    corr = default_correction('heating', pminput.name, pmoutput.name)
    assert_almost_equal(corr(pminput.value), pmoutput.value)


@pytest.mark.parametrize(
    "mode, pminput, pmoutput",
    [
        ('cooling', 'freq', 'COP'),
        ('cooling', 'freq', 'power'),
        ('cooling', 'SHR', None),
        ('heating', 'freq', 'COP'),
        ('heating', 'freq', 'power'),
    ]
)
def test_heating_corrections_asymptotic_behavior(mode, pminput, pmoutput):
    corr = default_correction(mode, pminput, pmoutput)
    assert np.isfinite(corr(np.inf))
