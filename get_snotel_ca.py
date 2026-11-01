#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Fetch daily snow-water-equivalent (SWE, NRCS element code WTEQ) for every
# California SNOTEL station, water years 1990-2026 (Oct 1989 - Jul 2026), from
# the NRCS Air & Water Database (AWDB) REST API. This is the ground-truth
# observed-snowpack counterpart to the ERA5-based Z500/T700 blocking/warm-
# event record in CA_z500_t700_blocking_events_detrend_5day.ipynb.
#
# Why not an ERA5-derived snow variable instead (SD/SMLT/ES, already in the
# archive used for Z500/T700)? Lundquist et al. 2026 ("Snow what? Comparing
# snow products...", Water Resources Research) benchmark global reanalyses
# against airborne-lidar SWE and find ERA5-Land (9 km) already has a -17.5%
# basin-scale bias and poor spatial fidelity in mountain terrain from its
# coarse resolution; they recommend 9 km or finer. Plain ERA5 (0.25 deg,
# ~28 km -- the only ERA5 resolution in this archive) is coarser still, so it
# is not a trustworthy stand-in for Sierra Nevada snowpack. SNOTEL stations are
# the actual point observations; see the notebook's intro for how gridded
# products (UA SWE/NSIDC-0719, SNODAS, UCLA WUS-SR) could extend this later.
#
# Usage: python get_snotel_ca.py
#
# Output (written to DATA_DIR, matching the Z500/T700 project's convention):
#   snotel_ca_stations.csv       -- station metadata (id, name, lat, lon, elev)
#   snotel_ca_swe_wy1990-2026.csv -- long-format daily SWE, all stations

import os

from awdb_fetch_lib import fetch_stations, fetch_swe

DATA_DIR = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'

# water years 1990-2026 = calendar range 1989-10-01 (start of WY1990) through
# 2026-07-31 (end of WY2026's melt season) -- matches the Z500/T700 notebook's
# 2026 out-of-sample convention, but extended to Oct-Jul (see notebook intro)
# since melt-out and any post-melt recovery mostly happen after April.
BEGIN_DATE = '1989-10-01'
END_DATE = '2026-07-31'


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print('Fetching CA SNOTEL station list ...')
    stations_df = fetch_stations('*:CA:SNTL', BEGIN_DATE, END_DATE)
    stations_csv = os.path.join(DATA_DIR, 'snotel_ca_stations.csv')
    stations_df.to_csv(stations_csv, index=False)
    print(f'{len(stations_df)} stations -> {stations_csv}')

    print(f'Fetching daily SWE (WTEQ), {BEGIN_DATE} to {END_DATE} ...')
    # one request for all stations x the full 1990-2026 period -- the AWDB API
    # handles this in a single call (tested: ~40 s, ~13 MB JSON for 36
    # stations x 36 years), no need to page by station or by year.
    swe_df = fetch_swe(stations_df['stationTriplet'], BEGIN_DATE, END_DATE)
    swe_csv = os.path.join(DATA_DIR, 'snotel_ca_swe_wy1990-2026.csv')
    swe_df.to_csv(swe_csv, index=False)
    print(f'{len(swe_df)} station-day SWE records -> {swe_csv}')


if __name__ == '__main__':
    main()
