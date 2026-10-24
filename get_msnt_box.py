#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Fetch daily snow-water-equivalent (SWE, NRCS element code WTEQ) for every
# MSNT ("Cooperator Snow Sensors") station falling inside the Sierra Nevada
# bounding box, water years 1990-2026, from the NRCS Air & Water Database
# (AWDB) REST API. Sibling of get_snotel_box.py (same API, same box, same
# WTEQ element) but network code MSNT instead of SNTL.
#
# MSNT stations are non-NRCS sensors (CA DWR, USBR, national parks, utilities,
# ranger districts) that report into AWDB and are served through the same
# pipeline and QC/QA flagging as SNOTEL -- unlike CDEC (get_cdec_box.py),
# which is raw unvalidated telemetry needing its own QC pass. In the Sierra
# box these 67 MSNT stations run continuously from 39.9N to 35.97N, covering
# the Yosemite/Mammoth/Kings Canyon/Sequoia terrain south of SNOTEL's ~38.1N
# limit -- but a station-ID/lat-lon crosswalk (see check_msnt_cdec_overlap.py)
# found all 67 already present in the CDEC pull under the same or a near-
# identical ID. So MSNT adds no new stations beyond CDEC; what it adds is a
# better-QC'd version of the ~65/67 stations CDEC also has, to prefer over
# CDEC's raw duplicate for those specific stations.
#
# Usage: python get_msnt_box.py
#
# Output (written to DATA_DIR, matching the Z500/T700 project's convention):
#   msnt_box_stations.csv       -- station metadata (id, name, lat, lon, elev)
#   msnt_box_swe_wy1990-2026.csv -- long-format daily SWE, all stations

import os
import time

import pandas as pd
import requests

API = 'https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1'
DATA_DIR = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'

# Sierra Nevada bounding box, ERA5 (0-360) longitude convention -- converted
# below to the -180/180 convention the AWDB API/station records use. Same box
# as get_snotel_box.py / get_cdec_box.py.
SIERRA_LAT_S, SIERRA_LAT_N = 34.5, 40.0
SIERRA_LON_W, SIERRA_LON_E = 239.0, 243.5
LON_W = SIERRA_LON_W - 360.0
LON_E = SIERRA_LON_E - 360.0

BEGIN_DATE = '1989-10-01'
END_DATE = '2026-05-31'

IN_MM = 25.4  # WTEQ is reported in inches; 1 in = 25.4 mm
CHUNK_SIZE = 10  # AWDB /data rejects/times out on a large batch of 36-year MSNT triplets


def fetch_stations():
    r = requests.get(
        f'{API}/stations',
        params={'stationTriplets': '*:*:MSNT', 'activeOnly': 'true'},
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
    triplets = list(triplets)
    records = []
    for i in range(0, len(triplets), CHUNK_SIZE):
        chunk = triplets[i:i + CHUNK_SIZE]
        r = requests.get(
            f'{API}/data',
            params={
                'stationTriplets': ','.join(chunk),
                'elements': 'WTEQ',
                'duration': 'DAILY',
                'beginDate': BEGIN_DATE,
                'endDate': END_DATE,
            },
            headers={'accept': 'application/json'},
            timeout=180,
        )
        r.raise_for_status()
        for station in r.json():
            triplet = station['stationTriplet']
            if not station['data']:
                continue
            for v in station['data'][0]['values']:
                val = v.get('value')
                if val is not None:
                    records.append((triplet, v['date'], val * IN_MM))
        time.sleep(0.3)  # be polite to the AWDB server between chunk requests
    return pd.DataFrame(records, columns=['stationTriplet', 'date', 'swe_mm'])


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print(f'Fetching MSNT stations in Sierra box '
          f'({SIERRA_LAT_S}-{SIERRA_LAT_N}N, {SIERRA_LON_W}-{SIERRA_LON_E}E) ...')
    stations_df = fetch_stations()
    stations_csv = os.path.join(DATA_DIR, 'msnt_box_stations.csv')
    stations_df.to_csv(stations_csv, index=False)
    print(f'{len(stations_df)} stations -> {stations_csv}')

    print(f'Fetching daily SWE (WTEQ), {BEGIN_DATE} to {END_DATE} ...')
    swe_df = fetch_swe(stations_df['stationTriplet'])
    swe_csv = os.path.join(DATA_DIR, 'msnt_box_swe_wy1990-2026.csv')
    swe_df.to_csv(swe_csv, index=False)
    print(f'{len(swe_df)} station-day SWE records -> {swe_csv}')


if __name__ == '__main__':
    main()
