"""Shared NRCS Air & Water Database (AWDB) REST API helpers for the station-SWE
fetch scripts (get_snotel_ca.py, get_snotel_box.py, get_msnt_box.py). These three
scripts query the same two endpoints (station list, daily data) and only differ in
their stationTriplets pattern, optional box filter, and (for MSNT) chunking --
pulling the shared logic here means a fix (like the activeOnly completeness issue
below) or an API quirk only has to be handled once.
"""

import time

import pandas as pd
import requests

API = 'https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1'
IN_MM = 25.4  # AWDB WTEQ is reported in inches; 1 in = 25.4 mm


def fetch_stations(triplet_pattern, begin_date, end_date, lat_range=None, lon_range=None, timeout=60):
    """Station metadata for every AWDB station matching `triplet_pattern` (e.g.
    '*:CA:SNTL', '*:*:MSNT'), restricted to stations whose [beginDate, endDate]
    overlaps [begin_date, end_date] rather than activeOnly=true, which silently
    drops stations decommissioned before today even if they have real data within
    the study period (verified live against AWDB: activeOnly=true drops 5 of 72
    in-box MSNT stations this way, some with records extending to 2016 -- well
    inside this project's study window).

    Pass lat_range=(south, north) and lon_range=(west, east) (AWDB's native
    -180/180 longitude convention) to additionally restrict to a geographic box.
    """
    r = requests.get(
        f'{API}/stations',
        params={'stationTriplets': triplet_pattern, 'activeOnly': 'false'},
        headers={'accept': 'application/json'},
        timeout=timeout,
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
            'endDate': s['endDate'][:10],
        }
        for s in stations
    ]).sort_values('stationTriplet').reset_index(drop=True)

    overlaps_period = (df['beginDate'] <= end_date) & (df['endDate'] >= begin_date)
    df = df[overlaps_period]

    if lat_range is not None:
        df = df[df['latitude'].between(*lat_range)]
    if lon_range is not None:
        df = df[df['longitude'].between(*lon_range)]

    return df.reset_index(drop=True)


def fetch_swe(triplets, begin_date, end_date, chunk_size=None, pace_s=0.0, timeout=180):
    """Daily WTEQ (snow-water-equivalent) values for `triplets`, [begin_date,
    end_date], as a long-format (stationTriplet, date, swe_mm) DataFrame.

    If `chunk_size` is given, splits the station list into chunks of that size,
    pausing `pace_s` seconds between chunk requests -- some AWDB station/duration
    combinations reject or time out on a single large multi-decade, many-station
    request (observed for MSNT; SNOTEL's smaller station counts handle it in one
    call).
    """
    triplets = list(triplets)
    chunks = [triplets] if chunk_size is None else [
        triplets[i:i + chunk_size] for i in range(0, len(triplets), chunk_size)
    ]

    records = []
    for chunk in chunks:
        r = requests.get(
            f'{API}/data',
            params={
                'stationTriplets': ','.join(chunk),
                'elements': 'WTEQ',
                'duration': 'DAILY',
                'beginDate': begin_date,
                'endDate': end_date,
            },
            headers={'accept': 'application/json'},
            timeout=timeout,
        )
        r.raise_for_status()
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
        if pace_s:
            time.sleep(pace_s)

    return pd.DataFrame(records, columns=['stationTriplet', 'date', 'swe_mm'])
