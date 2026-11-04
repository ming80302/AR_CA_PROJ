#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Cross-walk MSNT (get_msnt_box.py) stations against CDEC (get_cdec_box.py)
# stations in the Sierra box, by exact stationId match first, then by
# lat/lon proximity (<1 km, great-circle) for the rest. CDEC aggregates many
# operators including a duplicate feed of NRCS cooperator sensors, so the two
# station lists were expected to overlap -- this makes the overlap explicit
# and machine-readable instead of eyeballing it.
#
# Usage: python check_msnt_cdec_overlap.py
#   (run get_msnt_box.py and get_cdec_box.py first)
#
# Output (written to DATA_DIR):
#   msnt_cdec_overlap.csv -- one row per in-box MSNT station: its matching
#     CDEC stationId (if any), match_type ('exact_id', 'proximity', or
#     'none'), and the match distance in km for proximity matches.

import numpy as np
import pandas as pd

DATA_DIR = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'
PROXIMITY_KM = 1.0  # station match radius
EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. [Fixed 2026-11-04] Replaces a naive
    sqrt(dlat**2 + dlon**2) degree-space distance, which treats a degree of
    longitude as equal to a degree of latitude -- wrong by a factor of
    cos(lat) (~0.80 at this Sierra box's ~37N midpoint, i.e. 1 deg longitude
    is only ~80% as far as 1 deg latitude). That mismatch could misclassify
    a real ~1 km match as 'none' (longitude-dominant offset, under-counted)
    or accept a >1 km pair as 'proximity' (latitude-dominant offset,
    over-counted), depending on which direction the station offset ran.
    lat1/lon1 may be scalars; lat2/lon2 may be pandas Series (broadcasts)."""
    lat1, lon1, lat2, lon2 = (np.deg2rad(v) for v in (lat1, lon1, lat2, lon2))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def main():
    msnt = pd.read_csv(DATA_DIR + 'msnt_box_stations.csv')
    msnt['stationId'] = msnt['stationTriplet'].str.split(':').str[0]

    cdec = pd.read_csv(DATA_DIR + 'cdec_box_stations.csv')

    rows = []
    for _, m in msnt.iterrows():
        cdec_match = cdec[cdec['stationId'] == m['stationId']]
        if len(cdec_match):
            c = cdec_match.iloc[0]
            rows.append((m['stationTriplet'], m['name'], c['stationId'], c['name'],
                         'exact_id', 0.0))
            continue

        dist = haversine_km(m['latitude'], m['longitude'], cdec['latitude'], cdec['longitude'])
        j = dist.idxmin()
        if dist[j] < PROXIMITY_KM:
            c = cdec.loc[j]
            rows.append((m['stationTriplet'], m['name'], c['stationId'], c['name'],
                         'proximity', round(dist[j], 4)))
        else:
            rows.append((m['stationTriplet'], m['name'], None, None, 'none', None))

    overlap = pd.DataFrame(rows, columns=[
        'msnt_triplet', 'msnt_name', 'cdec_stationId', 'cdec_name', 'match_type', 'match_dist_km',
    ])

    counts = overlap['match_type'].value_counts()
    print(f'{len(overlap)} in-box MSNT stations; match breakdown: {counts.to_dict()}')
    print(f'MSNT stations with NO CDEC counterpart: {counts.get("none", 0)}')

    out_csv = DATA_DIR + 'msnt_cdec_overlap.csv'
    overlap.to_csv(out_csv, index=False)
    print(f'-> {out_csv}')


if __name__ == '__main__':
    main()
