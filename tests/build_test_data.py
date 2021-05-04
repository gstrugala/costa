"""
This module is not meant to be run when testing, but to generate data to
use for comparison in later tests.  It should be modified (and executed)
only when the expected output of the functions change (and thus also the
comparison data in tests).

"""

from pathlib import Path

import numpy as np
import pandas as pd

import costa


# Cooling
cm = costa.build_cooling_permap()
cm.pm.entries['freq'] = np.arange(0.1, 1.5, 0.1)
cm.pm.mode = 'cooling'
rated = pd.DataFrame({'capacity': [3.52], 'power': [0.79]})
cmf = cm.pm.fill(norm=rated)

# Heating
hm = costa.build_heating_permap()
hm.pm.entries['freq'] = np.arange(0.1, 2.1, 0.1)
hm.pm.mode = 'heating'
hm.pm.initial_norm_values['freq'] = 119 / 60
rated = pd.DataFrame({'capacity': [4.69], 'power': [1.01]})
hmf = hm.pm.fill(norm=rated)

# Write to files (uncomment line if you are sure to want to overwrite).
tests_dir = Path(__file__).parent
# cmf.to_pickle(tests_dir/"data/filled-table-cooling.pkl")
# hmf.to_pickle(tests_dir/"data/filled-table-heating.pkl")
