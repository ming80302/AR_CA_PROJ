#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Fetch daily snow-water-equivalent (SWE, NRCS element code WTEQ) for every
# SNOTEL station (any state) falling inside the Sierra Nevada bounding box,
# water years 1990-2026 (Oct 1989 - Jul 2026), from the NRCS Air & Water
# Database (AWDB) REST API. Variant of get_snotel_ca.py that filters by
# geographic box instead of state network code, so it also picks up stations
# just across the CA/NV border (e.g. the Tahoe basin).
#
# Usage: python get_snotel_box.py
#
# Output (written to DATA_DIR, matching the Z500/T700 project's convention):
#   snotel_box_stations.csv       -- station metadata (id, name, lat, lon, elev)
#   snotel_box_swe_wy1990-2026.csv -- long-format daily SWE, all stations
# Note: SWE is an impact variable, and the Sierra is where the vast majority of 
# California's meaningful snowpack and water-supply-relevant signal actually lives
# — the station network outside it is far sparser and climatologically different

import os

from awdb_fetch_lib import fetch_stations, fetch_swe

DATA_DIR = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'

# Sierra Nevada bounding box, ERA5 (0-360) longitude convention -- converted
# below to the -180/180 convention the AWDB API/station records use.
SIERRA_LAT_S, SIERRA_LAT_N = 34.5, 40.0
SIERRA_LON_W, SIERRA_LON_E = 239.0, 243.5
LON_W = SIERRA_LON_W - 360.0
LON_E = SIERRA_LON_E - 360.0

# water years 1990-2026 = calendar range 1989-10-01 (start of WY1990) through
# 2026-07-31 (end of WY2026's melt season) -- matches the Z500/T700 notebook's
# 2026 out-of-sample convention, but extended to Oct-Jul (see get_snotel_ca.py)
# since melt-out and any post-melt recovery mostly happen after April.
BEGIN_DATE = '1989-10-01'
END_DATE = '2026-07-31'


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print(f'Fetching SNOTEL stations in Sierra box '
          f'({SIERRA_LAT_S}-{SIERRA_LAT_N}N, {SIERRA_LON_W}-{SIERRA_LON_E}E) ...')
    # '*:*:SNTL' -- any state, network SNTL -- so stations just across the
    # CA/NV border (e.g. Tahoe basin) aren't missed; box-filtered below.
    stations_df = fetch_stations(
        '*:*:SNTL', BEGIN_DATE, END_DATE,
        lat_range=(SIERRA_LAT_S, SIERRA_LAT_N), lon_range=(LON_W, LON_E),
    )
    stations_csv = os.path.join(DATA_DIR, 'snotel_box_stations.csv')
    stations_df.to_csv(stations_csv, index=False)
    print(f'{len(stations_df)} stations -> {stations_csv}')

    print(f'Fetching daily SWE (WTEQ), {BEGIN_DATE} to {END_DATE} ...')
    # one request for all stations x the full 1990-2026 period -- the AWDB
    # API handles this in a single call, no need to page by station or year.
    swe_df = fetch_swe(stations_df['stationTriplet'], BEGIN_DATE, END_DATE)
    swe_csv = os.path.join(DATA_DIR, 'snotel_box_swe_wy1990-2026.csv')
    swe_df.to_csv(swe_csv, index=False)
    print(f'{len(swe_df)} station-day SWE records -> {swe_csv}')


if __name__ == '__main__':
    main()
