import pytest
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal
import matplotlib

import costa
from costa.defaults import build_default_corrections


@pytest.fixture
def permap(mode, manufacturer_data_file):
    if mode == 'cooling':
        return costa.build_cooling_permap(manufacturer_data_file)
    elif mode == 'heating':
        return costa.build_heating_permap(manufacturer_data_file)
    else:
        raise ValueError("'mode' should be either 'cooling' or 'heating'.")


@pytest.fixture
def complete_permap(mode, permap):
    min_freq, max_freq = 0.1, {'cooling': 1.5, 'heating': 2.1}[mode]
    freq_entries = np.arange(min_freq, max_freq, 0.1)
    permap.pm.entries['freq'] = freq_entries
    permap.pm.mode = mode
    if mode == 'heating':
        permap.pm.initial_norm_values['freq'] = 119 / 60
    rated = pd.DataFrame({
        'capacity': [{'cooling': 3.52, 'heating': 4.69}[mode]],
        'power': [{'cooling': 0.79, 'heating': 1.01}[mode]]
    })
    complete = permap.pm.fill(norm=rated)
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
    return costa.Permap


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
class TestPermap:
    def test_permap(self, permap):
        pm = costa.Permap(permap)
        assert isinstance(permap.pm, type(pm))

    def test_update_data(self, mode, permap):
        old_max, new_max = {'cooling': (32.2, 35), 'heating': (23.9, 25)}[mode]
        new = (
            (2 * permap.copy())
            .rename(index={old_max: new_max}, level='Tdbr')
            .pm.copyattr(permap)
        )
        new.index.set_names('Toa', level='Tdbo', inplace=True)
        updated = permap.pm.update_data(new)
        assert_frame_equal(updated, new)
        rng = new.pm.ranges
        rng['Tdbr'] = [rng['Tdbr'].left, new_max]
        rng = dict(rng)
        rng['Toa'] = rng.pop('Tdbo')
        assert updated.pm.ranges == rng
        assert updated.pm.restricted_levels.keys() == rng.keys()

    def test_ranges(self, permap):
        ranges = costa.Permap.index_ranges(permap.index)
        assert ranges == permap.pm.ranges

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

    def test_set_ranges(self, cls, permap):
        level = permap.index.names[0]
        levelrange = cls.index_range(permap.index, level)
        left, right = levelrange.left - levelrange.length / 2, levelrange.right
        # Test list assignment
        permap.pm.ranges[level] = [left, right]
        interval = pd.Interval(left, right, closed='both')
        assert permap.pm.ranges[level] == interval
        # Test interval consistency check
        left = levelrange.left + levelrange.length / 2
        with pytest.raises(RuntimeError):
            permap.pm.ranges[level] = [left, right]

    def test_pm(self, complete_permap, filled_table):
        assert_frame_equal(complete_permap, filled_table)

    def test_mode(self, mode, permap):
        assert permap.pm.corrections is None
        assert permap.pm.initial_norm_values is None
        permap.pm.mode = mode
        assert permap.pm.mode == mode
        assert isinstance(permap.pm.corrections, dict)
        assert isinstance(permap.pm.initial_norm_values, dict)

    def test_corrections(self, mode, permap):
        assert permap.pm.corrections is None
        default_corrections = build_default_corrections(mode)
        # Test setter
        permap.pm.corrections = default_corrections
        # Test getter
        freq_corr = permap.pm.corrections['freq']
        # Test deleter
        del permap.pm.corrections['freq']
        # Test setting corrections for a single input
        permap.pm.corrections['freq'] = freq_corr
        assert permap.pm.corrections['freq'] == freq_corr
        assert permap.pm.corrections == default_corrections

    def test_normalized(self, permap):
        assert not permap.pm.normalized

    def test_normalize(self, mode, permap):
        permap.pm.mode = mode  # required for normalization
        rated_values = pd.DataFrame({col: [1] for col in permap})
        permap_normalized = permap.pm.normalize(rated_values)
        assert permap_normalized.pm.normalized
        # Assert that trying to normalize more than once raises a RuntimeError
        with pytest.raises(RuntimeError):
            permap_normalized.pm.normalize(rated_values)

    def test_copy(self, permap):
        copy = permap.pm.copy()
        assert_frame_equal(permap, copy)
        assert all([
            getattr(permap.pm, attribute) == getattr(copy.pm, attribute)
            for attribute in costa.Permap._attributes_to_copy
        ])

    def test_entries(self, permap):
        assert isinstance(permap.pm.entries, dict)

    def test_get_correction(self, mode, permap):
        permap.pm.mode = mode
        assert isinstance(permap.pm.get_correction('freq'), dict)
        assert callable(permap.pm.get_correction('freq', 'power'))

    def test_set_correction(self, mode, permap):
        permap.pm.mode = mode
        corr = permap.pm.corrections['freq'].pop('power')
        # Ensure that the entry doesn't exist anymore
        with pytest.raises(KeyError):
            del permap.pm.corrections['freq']['power']
        permap.pm.set_correction('freq', 'power', corr, inplace=True)
        # Now the entry exists again:
        assert permap.pm.corrections['freq']['power'] is not None

    def test_set_corrections(self, mode, permap):
        permap.pm.mode = mode
        corrs = permap.pm.corrections.pop('freq')
        # Ensure that the entry doesn't exist anymore
        with pytest.raises(KeyError):
            del permap.pm.corrections['freq']
        permap = permap.pm.set_corrections('freq', corrs)
        # Now the entry exists again:
        assert permap.pm.corrections['freq'] is not None

    def test_initial_norm_values(self, permap):
        assert permap.pm.initial_norm_values is None
        # Test setter
        permap.pm.initial_norm_values = {'freq': 2}
        # Test getter
        assert permap.pm.initial_norm_values['freq'] == 2
        # Try modifying the value
        permap.pm.initial_norm_values['freq'] = 3
        assert permap.pm.initial_norm_values['freq'] == 3

    def test_check_mode(self, permap):
        with pytest.raises(RuntimeError):
            permap.pm._check_mode()

    def test_check_columns(self, permap):
        keys = list(permap.columns)
        # Alter columns
        keys[0] += " altered"
        with pytest.raises(ValueError):
            permap.pm._check_columns(keys)

    def test_check_corrections(self, mode, permap):
        permap.pm.mode = mode  # Automatiaclly sets default corrections
        del permap.pm.corrections['freq']['power']
        del permap.pm.corrections['freq']['COP']
        with pytest.raises(ValueError):
            permap.pm._check_corrections('freq')

    def test_add_correction(self, mode, permap):
        permap.pm.corrections = build_default_corrections(mode)
        with pytest.warns(UserWarning):
            permap.pm.mode = mode  # required for running _add_corrections
        assert len(permap.pm.corrections['freq'].keys()) == 2
        permap.pm._add_correction('freq', inplace=True)
        assert len(permap.pm.corrections['freq'].keys()) == 3

    def test_add_missing_df_column(self, permap):
        assert len(permap.columns) == 2
        extended = costa.Permap._add_missing_df_column(permap)
        assert len(extended.columns) == 3
        assert_series_equal(
            extended.COP,
            permap.capacity / permap.power,
            check_names=False
        )

    def test_correct(self, mode, permap, all_freq_corrections):
        permap.pm.mode = mode
        corrections = all_freq_corrections
        del corrections['COP']
        corrected = permap.pm.copy()
        for quantity, correction in corrections.items():
            #  Add correction(1) ~ 1 to avoid precision errors
            corrected[quantity] *= correction(0.5) / correction(1)
        assert_frame_equal(permap.pm.correct(corrections, 0.5), corrected)

    def test_extend(self, mode, permap, all_freq_corrections):
        permap.pm.mode = mode
        corrections = all_freq_corrections
        del corrections['COP']
        entries = [0.1, 0.5, 1, 1.5]
        extended = pd.concat(
            [permap.pm.correct(corrections, entry) for entry in entries],
            keys=entries,
            names=['freq']
        )
        assert_frame_equal(
            permap.pm.extend(corrections, entries, name='freq'),
            extended
        )

    def test_fill(self, mode, permap, filled_table):
        min_freq, max_freq = 0.1, {'cooling': 1.5, 'heating': 2.1}[mode]
        freq_entries = np.arange(min_freq, max_freq, 0.1)
        permap.pm.entries['freq'] = freq_entries
        permap.pm.mode = mode
        if mode == 'cooling':
            rated_values = pd.DataFrame({'capacity': [3.52], 'power': [0.79]})
        else:
            permap.pm.initial_norm_values['freq'] = 119 / 60
            rated_values = pd.DataFrame({'capacity': [4.69], 'power': [1.01]})
        filled_map = permap.pm.fill(norm=rated_values)
        assert_frame_equal(filled_map, filled_table)
        with pytest.warns(UserWarning):
            missing_freq = permap.pm.copy()
            del missing_freq.pm.corrections['freq']
            missing_freq.pm.fill(norm=rated_values)

    def test_plot(self, filled_table, no_param):
        fig, ax = filled_table.pm.plot(
            'Tdbo', 'sensible_capacity', freq=0.8, AFR=1, Tdbr=21.1, Twbr=15.6
        )
        self.assert_plot(fig, ax)
        fig, ax = filled_table.pm.plot(
            'freq', 'power', z='Tdbr',
            zaxis='legend',
            AFR=1, Twbr=15.6, Tdbo=35
        )
        self.assert_plot(fig, ax)
        fig, ax, colorbar = filled_table.pm.plot(
            'Twbr', 'latent_capacity', z='freq',
            AFR=1, Tdbr=21.1, Tdbo=35,
            return_cbar=True
        )
        self.assert_plot(fig, ax, colorbar)

    @staticmethod
    def assert_plot(fig, ax, colorbar=None):
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(ax, matplotlib.axes.SubplotBase)
        if colorbar:
            assert isinstance(colorbar, matplotlib.colorbar.Colorbar)
