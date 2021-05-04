import pytest
from pandas import read_pickle
from pandas.testing import assert_frame_equal

from costa.buildpermap import build_cooling_permap, build_heating_permap


@pytest.fixture
def manufacturer_table(mode, root):
    return read_pickle(root / f"tests/data/manufacturer-table-{mode}.pkl")


@pytest.mark.parametrize('mode', ['cooling', 'heating'])
def test_build_permap(mode, manufacturer_table, manufacturer_data_file):
    """Compare dataframe build from file to pickled ones"""
    build_permap = {'cooling': build_cooling_permap,
                    'heating': build_heating_permap}[mode]
    table = build_permap(manufacturer_data_file)
    assert_frame_equal(table, manufacturer_table)
