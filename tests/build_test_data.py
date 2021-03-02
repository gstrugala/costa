"""
This module is not meant to be run when testing, but to generate data to
use for comparison in later tests.  It should be modified (and executed)
only when the expected output of the functions change (and thus also the
comparison data in tests).

"""

import numpy as np
import pandas as pd

import fillomino as fmo


# Cooling
cm = fmo.build_cooling_permap()
cm.pmf.entries['freq'] = np.arange(1, 15)/10
cm.pmf.mode = 'cooling'
rated = pd.DataFrame({'capacity': [3.52], 'power': [0.79]})
cmf = cm.pmf.fill(norm=rated)

# Heating
hm = fmo.build_heating_permap()
hm.pmf.entries['freq'] = np.arange(1, 21)/10
hm.pmf.mode = 'heating'
hm.pmf.manval_factors['freq'] = 119 / 60
rated = pd.DataFrame({'capacity': [4.69], 'power': [1.01]})
hmf = hm.pmf.fill(norm=rated)

# Write to files (uncomment line if you are sure to want to overwrite).
# cmf.to_pickle("tests/data/filled-table-cooling.pkl")
# cmfr.to_pickle("tests/data/restricted-range-table-cooling.pkl")
# cmfer.to_pickle("tests/data/extended-range-table-cooling.pkl")
# hmf.to_pickle("tests/data/filled-table-heating.pkl")
# hmfr.to_pickle("tests/data/restricted-range-table-heating.pkl")
# hmfer.to_pickle("tests/data/extended-range-table-heating.pkl")
