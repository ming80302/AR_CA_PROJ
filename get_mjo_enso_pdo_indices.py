#!/usr/bin/env python3
# Ming Ge / Claude, Nov 2026
#
# Fetch three public large-scale background-state indices for the mechanism thread's
# "does background state (not just upstream precursor fields) predict ridging/warm-
# episode duration" check (CA_ridging_persistence_background_state.ipynb):
#   - ONI (Oceanic Nino Index, ENSO), monthly, NOAA PSL mirror of CPC's ONI_v5
#   - PDO (Pacific Decadal Oscillation), monthly, NOAA PSL/NCEI
#   - OMI (OLR-based MJO Index), daily PC1/PC2/amplitude, NOAA PSL
# All three are public, no auth, no project-specific bias in how NOAA computes them --
# unlike everything else in this project (ERA5 reanalysis, station networks), fetched
# here for the first time. Written to DATA_DIR as tidy CSVs so every downstream
# notebook reads a local file, not the network, matching every other fetch script's
# convention.
#
# Usage: python get_mjo_enso_pdo_indices.py
#
# Output: oni_index.csv, pdo_index.csv, omi_index.csv in DATA_DIR.

import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import requests

DATA_DIR = Path('/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking')
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}


def fetch_monthly_index(url, missing_code, out_name, label):
    """NOAA PSL's standard monthly-index text format: a header line with the
    start/end year, then one row per year (year, 12 monthly values), then a
    missing-code line and free-text footer. Parses only the year rows.
    """
    text = requests.get(url, headers=UA, timeout=30).text
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 13 and re.fullmatch(r'\d{4}', parts[0]):
            year = int(parts[0])
            vals = [float(v) for v in parts[1:]]
            rows.append((year, vals))
    long_rows = []
    for year, vals in rows:
        for month, v in enumerate(vals, start=1):
            long_rows.append({'year': year, 'month': month,
                               label: np.nan if abs(v - missing_code) < 1e-6 else v})
    df = pd.DataFrame(long_rows)
    df.to_csv(DATA_DIR / out_name, index=False)
    n_valid = df[label].notna().sum()
    print(f'{out_name}: {len(df)} months, {n_valid} valid, '
          f'{df.year.min()}-{df.year.max()} ({label} range '
          f'[{df[label].min():.2f}, {df[label].max():.2f}])')


def fetch_omi():
    """Daily OMI (OLR-based MJO Index) PC1/PC2/amplitude, NOAA PSL --
    columns: year, month, day, PC1, PC2, amplitude (no header row)."""
    url = 'https://psl.noaa.gov/mjo/mjoindex/omi.1x.txt'
    text = requests.get(url, headers=UA, timeout=30).text
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 6:
            continue
        try:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            pc1, pc2, amplitude = float(parts[3]), float(parts[4]), float(parts[5])
        except ValueError:
            continue
        rows.append({'date': pd.Timestamp(year, month, day), 'pc1': pc1, 'pc2': pc2,
                     'amplitude': amplitude})
    df = pd.DataFrame(rows).sort_values('date').reset_index(drop=True)
    df.to_csv(DATA_DIR / 'omi_index.csv', index=False)
    print(f'omi_index.csv: {len(df)} days, {df.date.min().date()}-{df.date.max().date()}')


if __name__ == '__main__':
    fetch_monthly_index('https://psl.noaa.gov/data/correlation/oni.data', -99.90,
                         'oni_index.csv', 'oni')
    fetch_monthly_index('https://psl.noaa.gov/data/correlation/pdo.data', -9.90,
                         'pdo_index.csv', 'pdo')
    fetch_omi()
