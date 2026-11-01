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
# box these 72 MSNT stations (2026-11-01: was 67 before fixing fetch_stations's
# activeOnly filter in awdb_fetch_lib.py, which silently dropped 5 stations
# decommissioned before today despite having real data in the 1990-2026 study
# period) run continuously from 39.9N to 35.97N, covering the Yosemite/Mammoth/
# Kings Canyon/Sequoia terrain south of SNOTEL's ~38.1N limit -- but a
# station-ID/lat-lon crosswalk (see check_msnt_cdec_overlap.py) found all 72
# already present in the CDEC pull under the same or a near-identical ID. So
# MSNT adds no new stations beyond CDEC; what it adds is a better-QC'd version
# of the stations CDEC also has, to prefer over CDEC's raw duplicate for those
# specific stations.
#
# Usage: python get_msnt_box.py
#
# Output (written to DATA_DIR, matching the Z500/T700 project's convention):
#   msnt_box_stations.csv       -- station metadata (id, name, lat, lon, elev)
#   msnt_box_swe_wy1990-2026.csv -- long-format daily SWE, all stations

import os

from awdb_fetch_lib import fetch_stations, fetch_swe

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

CHUNK_SIZE = 10  # AWDB /data rejects/times out on a large batch of 36-year MSNT triplets


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print(f'Fetching MSNT stations in Sierra box '
          f'({SIERRA_LAT_S}-{SIERRA_LAT_N}N, {SIERRA_LON_W}-{SIERRA_LON_E}E) ...')
    stations_df = fetch_stations(
        '*:*:MSNT', BEGIN_DATE, END_DATE,
        lat_range=(SIERRA_LAT_S, SIERRA_LAT_N), lon_range=(LON_W, LON_E),
    )
    stations_csv = os.path.join(DATA_DIR, 'msnt_box_stations.csv')
    stations_df.to_csv(stations_csv, index=False)
    print(f'{len(stations_df)} stations -> {stations_csv}')

    print(f'Fetching daily SWE (WTEQ), {BEGIN_DATE} to {END_DATE} ...')
    swe_df = fetch_swe(
        stations_df['stationTriplet'], BEGIN_DATE, END_DATE,
        chunk_size=CHUNK_SIZE, pace_s=0.3,  # be polite to the AWDB server between chunk requests
    )
    swe_csv = os.path.join(DATA_DIR, 'msnt_box_swe_wy1990-2026.csv')
    swe_df.to_csv(swe_csv, index=False)
    print(f'{len(swe_df)} station-day SWE records -> {swe_csv}')


if __name__ == '__main__':
    main()
