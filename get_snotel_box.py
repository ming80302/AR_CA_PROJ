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

import os

import pandas as pd
import requests

API = 'https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1'
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
END_DATE = '2026-05-31'

IN_MM = 25.4  # SNOTEL WTEQ is reported in inches; 1 in = 25.4 mm


def fetch_stations():
    # '*:*:SNTL' -- any state, network SNTL -- so stations just across the
    # CA/NV border (e.g. Tahoe basin) aren't missed; filter to the box below.
    r = requests.get(
        f'{API}/stations',
        params={'stationTriplets': '*:*:SNTL', 'activeOnly': 'true'},
        headers={'accept': 'application/json'},
        timeout=60,
    )
    r.raise_for_status()
    stations = r.json()
    df = pd.DataFrame([
        {
            'stationTriplet': s['stationTriplet'],
            'name': s['name'],
            'elevation_ft': s['elevation'],
            'latitude': s['latitude'],
            'longitude': s['longitude'],
            'beginDate': s['beginDate'][:10],
        }
        for s in stations
    ]).sort_values('stationTriplet').reset_index(drop=True)

    in_box = (
        df['latitude'].between(SIERRA_LAT_S, SIERRA_LAT_N)
        & df['longitude'].between(LON_W, LON_E)
    )
    return df[in_box].reset_index(drop=True)


def fetch_swe(triplets):
    # one request for all stations x the full 1990-2026 period -- the AWDB
    # API handles this in a single call, no need to page by station or year.
    r = requests.get(
        f'{API}/data',
        params={
            'stationTriplets': ','.join(triplets),
            'elements': 'WTEQ',
            'duration': 'DAILY',
            'beginDate': BEGIN_DATE,
            'endDate': END_DATE,
        },
        headers={'accept': 'application/json'},
        timeout=180,
    )
    r.raise_for_status()
    records = []
    for station in r.json():
        triplet = station['stationTriplet']
        if not station['data']:
            continue
        for v in station['data'][0]['values']:
            # a day with no reading omits 'value' entirely rather than
            # setting it to null -- treat both the same as missing.
            val = v.get('value')
            if val is not None:
                records.append((triplet, v['date'], val * IN_MM))
    return pd.DataFrame(records, columns=['stationTriplet', 'date', 'swe_mm'])


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print(f'Fetching SNOTEL stations in Sierra box '
          f'({SIERRA_LAT_S}-{SIERRA_LAT_N}N, {SIERRA_LON_W}-{SIERRA_LON_E}E) ...')
    stations_df = fetch_stations()
    stations_csv = os.path.join(DATA_DIR, 'snotel_box_stations.csv')
    stations_df.to_csv(stations_csv, index=False)
    print(f'{len(stations_df)} stations -> {stations_csv}')

    print(f'Fetching daily SWE (WTEQ), {BEGIN_DATE} to {END_DATE} ...')
    swe_df = fetch_swe(stations_df['stationTriplet'])
    swe_csv = os.path.join(DATA_DIR, 'snotel_box_swe_wy1990-2026.csv')
    swe_df.to_csv(swe_csv, index=False)
    print(f'{len(swe_df)} station-day SWE records -> {swe_csv}')


if __name__ == '__main__':
    main()
