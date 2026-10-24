#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Fetch daily/monthly snow-water-equivalent (SWE, CDEC sensor 3 "SNOW, WATER
# CONTENT") for every CDEC station in the Sierra Nevada bounding box, water
# years 1990-2026 (Oct 1989 - May 2026), from the California Data Exchange
# Center (CDEC) web services.
#
# Why this on top of get_snotel_box.py? SNOTEL (NRCS, queried by
# get_snotel_box.py) only has stations in the Tahoe/Carson/Walker corridor
# (~38-39.5N) -- the center and south of the Sierra box (Yosemite, Mammoth,
# Kings Canyon, Sequoia, Kern) has no SNOTEL footprint at all, historically or
# currently. That terrain is instead monitored by CA DWR's manual snow
# courses (surveyed ~monthly, CDEC duration code 'M') and by automated snow
# sensors run by DWR, USBR, national parks, utilities, and ranger districts
# (CDEC duration code 'D'). CDEC aggregates all of these (plus a duplicate
# copy of the NRCS SNOTEL feed) under one API, which is what this script uses.
#
# Unlike NRCS's AWDB (get_snotel_box.py), CDEC is a raw real-time telemetry
# clearinghouse, not a QC'd archive: besides the -9999 missing sentinel
# (dropped below), the fetched SWE still contains sensor noise (small
# negative values near zero -- harmless, clip to 0 if needed) and a long tail
# of implausible spikes/dropouts (orders of magnitude off). Apply your own
# physical-range QC downstream before using this for science.
#
# Usage: python get_cdec_box.py
#
# Output (written to DATA_DIR, matching the Z500/T700 project's convention):
#   cdec_box_stations.csv       -- station metadata (id, name, lat, lon, elev, operator)
#   cdec_box_swe_wy1990-2026.csv -- long-format SWE, all stations, 'D' and 'M' duration

import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

API = 'https://cdec.water.ca.gov/dynamicapp'
DATA_DIR = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'

# Sierra Nevada bounding box, ERA5 (0-360) longitude convention -- same box as
# get_snotel_box.py, converted to the -180/180 convention CDEC uses.
SIERRA_LAT_S, SIERRA_LAT_N = 34.5, 40.0
SIERRA_LON_W, SIERRA_LON_E = 239.0, 243.5
LON_W = SIERRA_LON_W - 360.0
LON_E = SIERRA_LON_E - 360.0

BEGIN_DATE = '1989-10-01'
END_DATE = '2026-05-31'

SENSOR_NUM = 3  # SNOW, WATER CONTENT
DUR_CODES = ['D', 'M']  # daily (automated sensors) and monthly (manual snow courses)
CHUNK_SIZE = 25  # stations per data request, keeps each response a manageable size

IN_MM = 25.4  # CDEC SNOW WC is reported in inches; 1 in = 25.4 mm
MISSING = -9999


def fetch_stations():
    r = requests.get(
        f'{API}/staSearch',
        params={
            'sensor_chk': 'on', 'sensor': SENSOR_NUM, 'dur': 'D',
            'active_chk': 'on', 'active': 'Y',
            'loc_chk': 'on', 'lon1': LON_W, 'lon2': LON_E, 'lat1': SIERRA_LAT_S, 'lat2': SIERRA_LAT_N,
            'nearby': '', 'basin': '', 'hydro': '', 'county': '', 'operator': '',
            'display': 'sta',
        },
        timeout=60,
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    rows = []
    for tr in soup.select('tbody tr'):
        tds = tr.find_all('td')
        if len(tds) < 8:
            continue
        rows.append({
            'stationId': tds[0].get_text(strip=True),
            'name': tds[1].get_text(strip=True),
            'longitude': float(tds[4].get_text(strip=True)),
            'latitude': float(tds[5].get_text(strip=True)),
            'elevation_ft': float(tds[6].get_text(strip=True).replace(',', '')),
            'operator': tds[7].get_text(strip=True),
        })
    return pd.DataFrame(rows).drop_duplicates('stationId').sort_values('stationId').reset_index(drop=True)


def fetch_swe(station_ids, dur_code):
    records = []
    for i in range(0, len(station_ids), CHUNK_SIZE):
        chunk = station_ids[i:i + CHUNK_SIZE]
        r = requests.get(
            f'{API}/req/JSONDataServlet',
            params={
                'Stations': ','.join(chunk),
                'SensorNums': SENSOR_NUM,
                'dur_code': dur_code,
                'Start': BEGIN_DATE,
                'End': END_DATE,
            },
            timeout=180,
        )
        r.raise_for_status()
        for v in r.json():
            val = v.get('value')
            if val is None or val == MISSING:
                continue
            # obsDate (actual survey/reading date) is missing on some recent,
            # still-provisional records -- fall back to the nominal date
            records.append((v['stationId'], dur_code, v['date'], v.get('obsDate', v['date']), val * IN_MM))
        time.sleep(0.2)  # be polite to the CDEC server between chunk requests
    return pd.DataFrame(records, columns=['stationId', 'duration', 'date', 'obs_date', 'swe_mm'])


def main():
    print(f'Fetching CDEC stations in Sierra box '
          f'({SIERRA_LAT_S}-{SIERRA_LAT_N}N, {SIERRA_LON_W}-{SIERRA_LON_E}E) ...')
    stations_df = fetch_stations()
    stations_csv = DATA_DIR + 'cdec_box_stations.csv'
    stations_df.to_csv(stations_csv, index=False)
    print(f'{len(stations_df)} stations -> {stations_csv}')

    swe_parts = []
    for dur_code in DUR_CODES:
        print(f'Fetching SWE (sensor {SENSOR_NUM}, dur_code={dur_code}), '
              f'{BEGIN_DATE} to {END_DATE} ...')
        swe_parts.append(fetch_swe(stations_df['stationId'].tolist(), dur_code))
    swe_df = pd.concat(swe_parts, ignore_index=True)
    swe_csv = DATA_DIR + 'cdec_box_swe_wy1990-2026.csv'
    swe_df.to_csv(swe_csv, index=False)
    print(f'{len(swe_df)} station-day/month SWE records -> {swe_csv}')


if __name__ == '__main__':
    main()
