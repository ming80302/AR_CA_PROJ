#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Cross-walk MSNT (get_msnt_box.py) stations against CDEC (get_cdec_box.py)
# stations in the Sierra box, by exact stationId match first, then by
# lat/lon proximity (<0.01 deg, ~1 km) for the rest. CDEC aggregates many
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
#     'none'), and the match distance in degrees for proximity matches.

import pandas as pd

DATA_DIR = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'
PROXIMITY_DEG = 0.01  # ~1 km at Sierra latitudes


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

        dist = ((cdec['latitude'] - m['latitude'])**2 + (cdec['longitude'] - m['longitude'])**2)**0.5
        j = dist.idxmin()
        if dist[j] < PROXIMITY_DEG:
            c = cdec.loc[j]
            rows.append((m['stationTriplet'], m['name'], c['stationId'], c['name'],
                         'proximity', round(dist[j], 4)))
        else:
            rows.append((m['stationTriplet'], m['name'], None, None, 'none', None))

    overlap = pd.DataFrame(rows, columns=[
        'msnt_triplet', 'msnt_name', 'cdec_stationId', 'cdec_name', 'match_type', 'match_dist_deg',
    ])

    counts = overlap['match_type'].value_counts()
    print(f'{len(overlap)} in-box MSNT stations; match breakdown: {counts.to_dict()}')
    print(f'MSNT stations with NO CDEC counterpart: {counts.get("none", 0)}')

    out_csv = DATA_DIR + 'msnt_cdec_overlap.csv'
    overlap.to_csv(out_csv, index=False)
    print(f'-> {out_csv}')


if __name__ == '__main__':
    main()
