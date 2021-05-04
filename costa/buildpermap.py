from pathlib import Path

import pandas as pd


def build_cooling_permap(datafile=None):
    """Read cooling performance map into an extendable DataFrame."""
    if datafile is None:
        parent = Path(__file__).parent
        datafile = parent/"resources/manufacturer-data-cooling.txt"
    data = pd.read_csv(datafile, sep=' ', skiprows=2).to_numpy()
    Tdbo, raw_data = data[:, 0], data[:, 1:]
    r = pd.read_csv(datafile, sep=' ', index_col=0, nrows=2, header=None)
    # Order is important as raw_data is formatted this way
    r = r.reindex(['Tdbr', 'Twbr'])
    col_headers = [
        (Tdbr, Twbr, P)
        for Tdbr, Twbr in r.to_numpy().T
        for P in ('capacity', 'sensible_capacity', 'power')
    ]
    level_names = ['Tdbr', 'Twbr', 'cooling']
    colidx = pd.MultiIndex.from_tuples(col_headers, names=level_names)
    rowidx = pd.Index(Tdbo, name='Tdbo')
    df = pd.DataFrame(raw_data, index=rowidx, columns=colidx)
    wrong_order = df.drop('sensible_capacity', axis='columns', level='cooling')
    right_order = wrong_order.reorder_levels(
        ['cooling', 'Tdbr', 'Twbr'], axis='columns'
    )
    permap = right_order.sort_index().stack().stack()
    return permap.reorder_levels(['Tdbr', 'Twbr', 'Tdbo']).sort_index()


def build_heating_permap(datafile=None):
    """Read heating performance map into an extendable DataFrame."""
    if datafile is None:
        parent = Path(__file__).parent
        datafile = parent/"resources/manufacturer-data-heating.txt"
    data = pd.read_csv(datafile, sep=' ', skiprows=1).to_numpy()
    Tdbo, raw_data = data[:, 0], data[:, 2:]
    Tdbr = pd.read_csv(datafile, sep=' ', nrows=1, header=None).iloc[0, 1:]
    # Capacity must come before input power as raw_data is formatted this way
    col_headers = [
        (T, P) for T in Tdbr.to_numpy() for P in ('capacity', 'power')
    ]
    level_names = ['Tdbr', 'heating']
    colidx = pd.MultiIndex.from_tuples(col_headers, names=level_names)
    rowidx = pd.Index(Tdbo, name='Tdbo')
    df = pd.DataFrame(raw_data, index=rowidx, columns=colidx)
    wrong_format = df.swaplevel('Tdbr', 'heating', axis=1).sort_index(axis=1)
    wrong_format.T.unstack().T.swaplevel('Tdbo', 'Tdbr').sort_index()
    return wrong_format.T.unstack().T.swaplevel('Tdbo', 'Tdbr').sort_index()
