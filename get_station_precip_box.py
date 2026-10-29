#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Fetch daily precipitation for the Sierra Nevada station network already used in
# CA_snowmelt_events_detrend_5day.ipynb (combined_sierra_stations.csv /
# combined_sierra_swe_wy1990-2026.csv), to let that notebook's ERA5-based "implied
# rain" (tp - sf) dry/wet rain-on-snow classification be checked against actual
# station-measured precipitation instead of just assumed reliable.
#
# Why this wasn't already fetched: get_snotel_box.py / get_msnt_box.py / get_cdec_box.py
# only ever requested SWE (WTEQ / CDEC sensor 3). Availability turns out to be very
# uneven across the three source networks:
#   SNTL (NRCS, element PRCP)        -- all 36 of 36 daily-reporting stations
#   MSNT ("Cooperator Snow Sensors") -- 0 of 67: this network has no precipitation
#                                        gauge at all, only SWE sensors
#   CDEC (sensor 45, fallback 2)     -- a handful of the 44 daily-reporting candidates
# So only ~41 of the 147 daily-reporting Sierra stations (28%) have any precipitation
# measurement, concentrated in the SNOTEL-covered northern Sierra; MSNT's entire
# southern-Sierra footprint (Yosemite/Mammoth/Kings Canyon/Sequoia/Kern) has none.
# That's a real coverage gap for a station-based cross-check, not a reason to skip it
# -- see the notebook's Section 5c-adjacent validation cell for how this is handled
# (an aggregate cross-check over the stations that do report, not a full replacement
# of the ERA5-based classification).
#
# CDEC's JSONDataServlet has been observed to time out on a single ~36-year-range
# request even for a handful of stations -- fetched in 5-year chunks here with
# retries, unlike get_cdec_box.py's single-shot SWE fetch (sensor 3 apparently
# doesn't hit the same limit).
#
# Usage: python get_station_precip_box.py
#
# Output (written to DATA_DIR, matching the project's convention):
#   station_precip_box_stations.csv       -- which of the 147 daily-reporting
#                                             stations have a precipitation
#                                             measurement, and from which source
#   station_precip_box_wy1990-2025.csv    -- long-format daily precipitation (mm),
#                                             all stations with any precip data

import time

import pandas as pd
import requests

AWDB_API = 'https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1'
CDEC_API = 'https://cdec.water.ca.gov/dynamicapp'
DATA_DIR = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'

BEGIN_DATE = '1989-10-01'
END_DATE = '2025-05-31'   # matches the notebook's fit period (water years 1990-2025)

IN_MM = 25.4  # both AWDB PRCP and CDEC precip sensors report in inches


def load_daily_reporting_stations():
    stations = pd.read_csv(DATA_DIR + 'combined_sierra_stations.csv')
    swe_long = pd.read_csv(DATA_DIR + 'combined_sierra_swe_wy1990-2026.csv')
    daily_ids = set(swe_long.loc[swe_long.duration == 'D', 'station_id'])
    return stations[stations.station_id.isin(daily_ids)].copy()


def fetch_awdb_prcp(triplets):
    """AWDB PRCP element for a list of SNTL/MSNT station triplets. Returns a
    long-format (station_id, date, prcp_mm) frame for whichever triplets actually
    have a PRCP element configured -- determined by what the /stations endpoint
    returns when filtered on elements=PRCP, not assumed from network membership.
    """
    if not triplets:
        return pd.DataFrame(columns=['station_id', 'date', 'prcp_mm'])

    r = requests.get(f'{AWDB_API}/stations',
                      params={'stationTriplets': ','.join(triplets), 'elements': 'PRCP', 'activeOnly': 'false'},
                      headers={'accept': 'application/json'}, timeout=60)
    r.raise_for_status()
    have_prcp = [s['stationTriplet'] for s in r.json()]
    if not have_prcp:
        return pd.DataFrame(columns=['station_id', 'date', 'prcp_mm'])

    r = requests.get(f'{AWDB_API}/data',
                      params={'stationTriplets': ','.join(have_prcp), 'elements': 'PRCP', 'duration': 'DAILY',
                              'beginDate': BEGIN_DATE, 'endDate': END_DATE},
                      headers={'accept': 'application/json'}, timeout=180)
    r.raise_for_status()
    records = []
    for station in r.json():
        if not station['data']:
            continue
        for v in station['data'][0]['values']:
            val = v.get('value')
            if val is not None:
                records.append((station['stationTriplet'], v['date'], val * IN_MM))
    return pd.DataFrame(records, columns=['station_id', 'date', 'prcp_mm'])


def fetch_cdec_precip(station_ids):
    """CDEC precipitation (sensor 45, PRECIPITATION INCREMENTAL; fall back to sensor 2,
    PRECIPITATION ACCUMULATED, differenced to a daily increment, for stations that
    only report the accumulated version) for a list of CDEC station IDs. Fetched in
    5-year chunks with retries -- a single request spanning the full 1990-2025 range
    has been observed to time out even for a handful of stations.
    """
    if not station_ids:
        return pd.DataFrame(columns=['station_id', 'date', 'prcp_mm'])

    year_chunks = [(y, min(y + 4, 2025)) for y in range(1990, 2026, 5)]
    raw = []
    for sensor in [45, 2]:
        for y0, y1 in year_chunks:
            start, end = f'{y0 - 1}-10-01', f'{y1}-05-31'
            for attempt in range(3):
                try:
                    r = requests.get(f'{CDEC_API}/req/JSONDataServlet',
                                      params={'Stations': ','.join(station_ids), 'SensorNums': sensor,
                                              'dur_code': 'D', 'Start': start, 'End': end},
                                      timeout=60)
                    data = r.json()
                    raw.extend({**v, 'sensor': sensor} for v in data)
                    break
                except Exception as e:
                    print(f'  CDEC sensor {sensor} {start}-{end} attempt {attempt}: {e}')
                    time.sleep(3)
            time.sleep(0.3)

    raw_df = pd.DataFrame(raw)
    if raw_df.empty:
        return pd.DataFrame(columns=['station_id', 'date', 'prcp_mm'])
    raw_df = raw_df[raw_df['value'].notna() & (raw_df['value'] != -9999)]

    parts = []
    for sid, g in raw_df.groupby('stationId'):
        g45 = g[g.sensor == 45]
        if len(g45) > 20:  # prefer incremental if it has real coverage
            parts.append(g45[['date', 'value']].assign(station_id=sid))
        else:
            g2 = g[g.sensor == 2].sort_values('date').copy()
            g2['value'] = g2['value'].diff().clip(lower=0)  # accumulated -> daily increment
            parts.append(g2[['date', 'value']].assign(station_id=sid))
    out = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=['date', 'value', 'station_id'])
    out['prcp_mm'] = out['value'] * IN_MM
    # CDEC returns dates as 'YYYY-M-D HH:MM' (unpadded, with a time component) vs.
    # AWDB's plain 'YYYY-MM-DD' -- normalize here so the merged output has one
    # consistent, directly-parseable date format rather than silently breaking
    # pd.read_csv(parse_dates=...) downstream on the mixed-format column.
    out['date'] = pd.to_datetime(out['date']).dt.strftime('%Y-%m-%d')
    return out[['station_id', 'date', 'prcp_mm']]


def main():
    daily_stations = load_daily_reporting_stations()
    print(f'{len(daily_stations)} daily-reporting Sierra stations, by source:')
    print(daily_stations.source.value_counts().to_dict())

    awdb_triplets = daily_stations.loc[daily_stations.source.isin(['SNTL', 'MSNT']), 'station_id'].tolist()
    print(f'\nChecking AWDB PRCP availability for {len(awdb_triplets)} SNTL+MSNT stations...')
    awdb_prcp = fetch_awdb_prcp(awdb_triplets)
    print(f'{awdb_prcp.station_id.nunique()} of {len(awdb_triplets)} have PRCP data '
          f'({len(awdb_prcp)} station-day records)')

    cdec_ids = daily_stations.loc[daily_stations.source == 'CDEC', 'station_id'].tolist()
    print(f'\nFetching CDEC precipitation for {len(cdec_ids)} CDEC-D candidates '
          '(chunked by 5-year period, with retries)...')
    cdec_prcp = fetch_cdec_precip(cdec_ids)
    print(f'{cdec_prcp.station_id.nunique()} of {len(cdec_ids)} CDEC stations have precip data '
          f'({len(cdec_prcp)} station-day records)')

    precip = pd.concat([awdb_prcp, cdec_prcp], ignore_index=True)
    precip = precip.groupby(['station_id', 'date'], as_index=False)['prcp_mm'].mean()

    have_precip_ids = set(precip.station_id.unique())
    stations_out = daily_stations[daily_stations.station_id.isin(have_precip_ids)][
        ['station_id', 'name', 'source', 'elevation_ft', 'latitude', 'longitude']
    ].copy()

    print(f'\n{len(stations_out)} of {len(daily_stations)} daily-reporting Sierra stations '
          f'({100 * len(stations_out) / len(daily_stations):.0f}%) have some precipitation data, by source:')
    print(stations_out.source.value_counts().to_dict())

    stations_csv = DATA_DIR + 'station_precip_box_stations.csv'
    stations_out.sort_values(['source', 'station_id']).to_csv(stations_csv, index=False)
    print(f'-> {stations_csv}')

    precip_csv = DATA_DIR + 'station_precip_box_wy1990-2025.csv'
    precip.sort_values(['station_id', 'date']).to_csv(precip_csv, index=False)
    print(f'-> {precip_csv}')


if __name__ == '__main__':
    main()
