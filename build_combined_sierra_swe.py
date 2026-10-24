#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Build one deduplicated, QC'd daily-SWE dataset for the full Sierra Nevada
# box (34.5-40.0N, 121-116.5W) by combining three station sources:
#
#   SNTL  (get_snotel_box.py)  -- north of ~38.1N, NRCS SNOTEL, AWDB-QC'd
#   MSNT  (get_msnt_box.py)    -- south of ~38.1N (Yosemite/Mammoth/Kings
#                                 Canyon/Sequoia/Kern), NRCS cooperator
#                                 sensors, AWDB-QC'd
#   CDEC  (get_cdec_box.py +   -- same southern terrain, but raw CDEC
#          qc_cdec_swe.py)        telemetry with heuristic QC applied here
#
# check_msnt_cdec_overlap.py found all 67 in-box MSNT stations already
# present in the CDEC pull (65 exact stationId match, 2 by lat/lon
# proximity -- BLC2/BLC, TES/TGP). For those overlapping stations we prefer
# the MSNT (AWDB-QC'd) version over CDEC's raw duplicate; the ~208 remaining
# CDEC stations (DWR, USBR, utilities, parks, ranger districts -- no AWDB
# counterpart) are kept from the QC'd CDEC feed since they're the only
# source for that coverage.
#
# Usage: python build_combined_sierra_swe.py
#   (run get_snotel_box.py, get_msnt_box.py, get_cdec_box.py, qc_cdec_swe.py,
#   and check_msnt_cdec_overlap.py first)
#
# Output (written to DATA_DIR):
#   combined_sierra_stations.csv        -- id, name, lat, lon, elev_ft, source
#   combined_sierra_swe_wy1990-2026.csv -- long-format: station_id, date,
#     swe_mm, source, duration

import pandas as pd

DATA_DIR = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'


def load_sntl():
    stations = pd.read_csv(DATA_DIR + 'snotel_box_stations.csv')
    swe = pd.read_csv(DATA_DIR + 'snotel_box_swe_wy1990-2026.csv', parse_dates=['date'])

    stations_out = stations.rename(columns={'stationTriplet': 'station_id'})[
        ['station_id', 'name', 'latitude', 'longitude', 'elevation_ft']
    ].assign(source='SNTL')
    swe_out = swe.rename(columns={'stationTriplet': 'station_id'})[
        ['station_id', 'date', 'swe_mm']
    ].assign(source='SNTL', duration='D')
    return stations_out, swe_out


def load_msnt():
    stations = pd.read_csv(DATA_DIR + 'msnt_box_stations.csv')
    swe = pd.read_csv(DATA_DIR + 'msnt_box_swe_wy1990-2026.csv', parse_dates=['date'])

    stations_out = stations.rename(columns={'stationTriplet': 'station_id'})[
        ['station_id', 'name', 'latitude', 'longitude', 'elevation_ft']
    ].assign(source='MSNT')
    swe_out = swe.rename(columns={'stationTriplet': 'station_id'})[
        ['station_id', 'date', 'swe_mm']
    ].assign(source='MSNT', duration='D')
    return stations_out, swe_out


def load_cdec_excluding_msnt_overlap():
    stations = pd.read_csv(DATA_DIR + 'cdec_box_stations.csv')
    swe = pd.read_csv(DATA_DIR + 'cdec_box_swe_wy1990-2026_qc.csv')
    swe['date'] = pd.to_datetime(swe['date'], format='mixed')
    swe = swe[swe['qc_flag'] != 'dropped'].drop(columns=['obs_date', 'qc_flag'])

    overlap = pd.read_csv(DATA_DIR + 'msnt_cdec_overlap.csv')
    covered_by_msnt = set(overlap['cdec_stationId'].dropna())
    print(f'Excluding {len(covered_by_msnt)} CDEC stations already covered (better-QC\'d) by MSNT')

    stations = stations[~stations['stationId'].isin(covered_by_msnt)]
    swe = swe[~swe['stationId'].isin(covered_by_msnt)]

    stations_out = stations.rename(columns={'stationId': 'station_id'})[
        ['station_id', 'name', 'latitude', 'longitude', 'elevation_ft']
    ].assign(source='CDEC')
    swe_out = swe.rename(columns={'stationId': 'station_id'})[
        ['station_id', 'date', 'swe_mm', 'duration']
    ].assign(source='CDEC')
    return stations_out, swe_out


def main():
    sntl_st, sntl_swe = load_sntl()
    msnt_st, msnt_swe = load_msnt()
    cdec_st, cdec_swe = load_cdec_excluding_msnt_overlap()

    stations = pd.concat([sntl_st, msnt_st, cdec_st], ignore_index=True)
    swe = pd.concat([sntl_swe, msnt_swe, cdec_swe], ignore_index=True)

    print(f'Combined stations by source: {stations["source"].value_counts().to_dict()}')
    print(f'Combined station-records by source: {swe["source"].value_counts().to_dict()}')
    print(f'{stations["station_id"].nunique()} unique stations, '
          f'lat range {stations.latitude.min():.2f}-{stations.latitude.max():.2f}N')

    stations_csv = DATA_DIR + 'combined_sierra_stations.csv'
    stations.sort_values(['source', 'station_id']).to_csv(stations_csv, index=False)
    print(f'-> {stations_csv}')

    swe_csv = DATA_DIR + 'combined_sierra_swe_wy1990-2026.csv'
    swe.sort_values(['station_id', 'date']).to_csv(swe_csv, index=False)
    print(f'-> {swe_csv}')


if __name__ == '__main__':
    main()
