import pytest
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

import fillomino as fmo
from fillomino.defaults import build_default_corrections


@pytest.fixture
def permap(mode, manufacturer_data_file):
    if mode == 'cooling':
        return fmo.build_cooling_permap(manufacturer_data_file)
    elif mode == 'heating':
        return fmo.build_heating_permap(manufacturer_data_file)
    else:
        raise ValueError("'mode' should be either 'cooling' or 'heating'.")


@pytest.fixture
def complete_permap(mode, permap):
    freq_entries = np.arange(1, {'cooling': 15, 'heating': 21}[mode]) / 10
    permap.pmf.entries['freq'] = freq_entries
    permap.pmf.mode = mode
    if mode == 'heating':
        permap.pmf.manval_factors['freq'] = 119 / 60
    rated = pd.DataFrame({
        'capacity': [{'cooling': 3.52, 'heating': 4.69}[mode]],
        'power': [{'cooling': 0.79, 'heating': 1.01}[mode]]
    })
    complete = permap.pmf.fill(norm=rated)
    return complete


@pytest.fixture
def all_freq_corrections(mode):
    corrections = build_default_corrections(mode).pop('freq')
    cop, power = corrections['COP'], corrections['power']

    def capacity(x):
        return power(x) * cop(x)

    return corrections | {'capacity': capacity}


@pytest.fixture
def cls():
    return fmo.PermapFiller


@pytest.fixture
def index_sample():
    index_entries = [[22, 24, 36, 45], [342, 548, 723, 927]]
    level_names = ('temperature', 'flowrate')
    return pd.MultiIndex.from_arrays(index_entries, names=level_names)


@pytest.fixture
def filled_table(mode, root):
    return pd.read_pickle(root / f"tests/data/filled-table-{mode}.pkl")


@pytest.fixture
def no_param(mode):
    if mode == 'heating':
        pytest.skip("operating mode has no influence on this test.")


@pytest.mark.parametrize('mode', ['cooling', 'heating'])
class TestPermapFiller:
    def test_permapfiller(self, permap):
        pmf = fmo.PermapFiller(permap)
        assert isinstance(permap.pmf, type(pmf))

    def test_update_data(self, mode, permap):
        old_max, new_max = {'cooling': (32.2, 35), 'heating': (23.9, 25)}[mode]
        new = (
            (2 * permap.copy())
            .rename(index={old_max: new_max}, level='Tdbr')
            .pmf.copyattr(permap)
        )
        new.index.set_names('Toa', level='Tdbo', inplace=True)
        updated = permap.pmf.update_data(new)
        assert_frame_equal(updated, new)
        rng = new.pmf.ranges
        rng['Tdbr'] = [rng['Tdbr'].left, new_max]
        rng = dict(rng)
        rng['Toa'] = rng.pop('Tdbo')
        assert updated.pmf.ranges == rng
        assert updated.pmf.restricted_levels.keys() == rng.keys()

    def test_ranges(self, permap):
        ranges = fmo.PermapFiller.index_ranges(permap.index)
        assert ranges == permap.pmf.ranges

    def test_index_range(self, cls, index_sample, no_param):
        level_values = index_sample.get_level_values('flowrate')
        rng = pd.Interval(level_values.min(), level_values.max(), 'both')
        assert cls.index_range(index_sample, 'flowrate') == rng

    def test_index_ranges(self, cls, index_sample, no_param):
        ranges = {
            'temperature': pd.Interval(22, 45, closed='both'),
            'flowrate': pd.Interval(342, 927, closed='both')
        }
        assert cls.index_ranges(index_sample) == ranges

    def test_pm(self, complete_permap, filled_table):
        assert_frame_equal(complete_permap, filled_table)

    def test_mode(self, mode, permap):
        assert permap.pmf.corrections is None
        assert permap.pmf.manval_factors is None
        permap.pmf.mode = mode
        assert permap.pmf.mode == mode
        assert isinstance(permap.pmf.corrections, dict)
        assert isinstance(permap.pmf.manval_factors, dict)

    def test_corrections(self, mode, permap):
        assert permap.pmf.corrections is None
        default_corrections = build_default_corrections(mode)
        # Test setter
        permap.pmf.corrections = default_corrections
        # Test getter
        freq_corr = permap.pmf.corrections['freq']
        # Test deleter
        del permap.pmf.corrections['freq']
        # Test setting corrections for a single input
        permap.pmf.corrections['freq'] = freq_corr
        assert permap.pmf.corrections['freq'] == freq_corr
        assert permap.pmf.corrections == default_corrections

    def test_normalized(self, permap):
        assert not permap.pmf.normalized

    def test_normalize(self, mode, permap):
        permap.pmf.mode = mode  # required for normalization
        rated_values = pd.DataFrame({col: [1] for col in permap})
        permap_normalized = permap.pmf.normalize(rated_values)
        assert permap_normalized.pmf.normalized
        # Assert that trying to normalize more than once raises a RuntimeError
        with pytest.raises(RuntimeError):
            permap_normalized.pmf.normalize(rated_values)

    def test_copy(self, permap):
        copy = permap.pmf.copy()
        assert_frame_equal(permap, copy)
        assert all([
            getattr(permap.pmf, attribute) == getattr(copy.pmf, attribute)
            for attribute in fmo.PermapFiller._attributes_to_copy
        ])

    def test_entries(self, permap):
        assert isinstance(permap.pmf.entries, dict)

    def test_get_correction(self, mode, permap):
        permap.pmf.mode = mode
        assert isinstance(permap.pmf.get_correction('freq'), dict)
        assert callable(permap.pmf.get_correction('freq', 'power'))

    def test_set_correction(self, mode, permap):
        permap.pmf.mode = mode
        corr = permap.pmf.corrections['freq'].pop('power')
        # Ensure that the entry doesn't exist anymore
        with pytest.raises(KeyError):
            del permap.pmf.corrections['freq']['power']
        permap.pmf.set_correction('freq', 'power', corr, inplace=True)
        # Now the entry exists again:
        assert permap.pmf.corrections['freq']['power'] is not None

    def test_set_corrections(self, mode, permap):
        permap.pmf.mode = mode
        corrs = permap.pmf.corrections.pop('freq')
        # Ensure that the entry doesn't exist anymore
        with pytest.raises(KeyError):
            del permap.pmf.corrections['freq']
        permap = permap.pmf.set_corrections('freq', corrs)
        # Now the entry exists again:
        assert permap.pmf.corrections['freq'] is not None

    def test_manval_factors(self, permap):
        assert permap.pmf.manval_factors is None
        # Test setter
        permap.pmf.manval_factors = {'freq': 2}
        # Test getter
        assert permap.pmf.manval_factors['freq'] == 2
        # Try modifying the value
        permap.pmf.manval_factors['freq'] = 3
        assert permap.pmf.manval_factors['freq'] == 3

    def test_check_mode(self, permap):
        with pytest.raises(RuntimeError):
            permap.pmf._check_mode()

    def test_check_columns(self, permap):
        keys = list(permap.columns)
        # Alter columns
        keys[0] += " altered"
        with pytest.raises(ValueError):
            permap.pmf._check_columns(keys)

    def test_check_corrections(self, mode, permap):
        permap.pmf.mode = mode  # Automatiaclly sets default corrections
        del permap.pmf.corrections['freq']['power']
        del permap.pmf.corrections['freq']['COP']
        with pytest.raises(ValueError):
            permap.pmf._check_corrections('freq')

    def test_add_correction(self, mode, permap):
        permap.pmf.corrections = build_default_corrections(mode)
        with pytest.warns(UserWarning):
            permap.pmf.mode = mode  # required for running _add_corrections
        assert len(permap.pmf.corrections['freq'].keys()) == 2
        permap.pmf._add_correction('freq', inplace=True)
        assert len(permap.pmf.corrections['freq'].keys()) == 3

    def test_add_missing_df_column(self, permap):
        assert len(permap.columns) == 2
        extended = fmo.PermapFiller._add_missing_df_column(permap)
        assert len(extended.columns) == 3
        assert_series_equal(
            extended.COP,
            permap.capacity / permap.power,
            check_names=False
        )

    def test_correct(self, mode, permap, all_freq_corrections):
        permap.pmf.mode = mode
        corrections = all_freq_corrections
        del corrections['COP']
        corrected = permap.pmf.copy()
        for quantity, correction in corrections.items():
            #  Add correction(1) ~ 1 to avoid precision errors
            corrected[quantity] *= correction(0.5) / correction(1)
        assert_frame_equal(permap.pmf.correct(corrections, 0.5), corrected)

    def test_extend(self, mode, permap, all_freq_corrections):
        permap.pmf.mode = mode
        corrections = all_freq_corrections
        del corrections['COP']
        entries = [0.1, 0.5, 1, 1.5]
        extended = pd.concat(
            [permap.pmf.correct(corrections, entry) for entry in entries],
            keys=entries,
            names=['freq']
        )
        assert_frame_equal(
            permap.pmf.extend(corrections, entries, name='freq'),
            extended
        )

    def test_fill(self, mode, permap, filled_table):
        freq_entries = np.arange(1, {'cooling': 15, 'heating': 21}[mode]) / 10
        permap.pmf.entries['freq'] = freq_entries
        permap.pmf.mode = mode
        if mode == 'cooling':
            rated_values = pd.DataFrame({'capacity': [3.52], 'power': [0.79]})
        else:
            permap.pmf.manval_factors['freq'] = 119 / 60
            rated_values = pd.DataFrame({'capacity': [4.69], 'power': [1.01]})
        filled_map = permap.pmf.fill(norm=rated_values)
        assert_frame_equal(filled_map, filled_table)
