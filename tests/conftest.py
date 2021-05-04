from pkg_resources import resource_filename
from pathlib import Path

import pytest


@pytest.fixture
def root():
    """Set up project root directory."""
    return Path(resource_filename('costa', '')).parent


@pytest.fixture
def manufacturer_data_file(mode, root):
    """Find data file even when current working dir is 'tests'."""
    relpath = f"costa/resources/manufacturer-data-{mode}.txt"
    return root / relpath
