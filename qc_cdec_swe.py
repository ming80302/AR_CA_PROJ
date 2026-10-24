#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Quality-control pass on the raw CDEC SWE pull from get_cdec_box.py. Unlike
# NRCS's AWDB (snotel_box_swe_*.csv), CDEC is raw real-time telemetry with no
# QC applied upstream: besides the -9999 missing sentinel (already dropped by
# get_cdec_box.py), it contains sensor noise (small negative values near
# zero -- normal pillow/sensor drift) and a thin tail of physically
# impossible spikes/dropouts (sensor malfunction, multiple orders of
# magnitude off -- e.g. a station reading >1e7 mm, or a mid-summer plateau
# around 4800 mm with no accumulation/melt signal).
#
# Two rules, both just physical-plausibility checks (no station-specific
# tuning):
#   1. -NEG_NOISE_MM <= swe_mm < 0  -> clipped to 0 (sensor baseline drift;
#      SWE cannot be negative, and sub-inch negative noise is routine for
#      pressure-pillow sensors sitting at true zero).
#   2. swe_mm < -NEG_NOISE_MM, or swe_mm > MAX_PLAUSIBLE_MM -> dropped (set to
#      NaN, row kept with a flag). MAX_PLAUSIBLE_MM is set well above the
#      highest credible Sierra SWE on record (~2200 mm, 2023's exceptional
#      year) so this only removes implausible outliers, not real extremes.
#
# Usage: python qc_cdec_swe.py
#
# Output (written to DATA_DIR):
#   cdec_box_swe_wy1990-2026_qc.csv -- same columns as the raw file, plus
#     'qc_flag' ('ok', 'clipped', 'dropped'); swe_mm is NaN where dropped.

import pandas as pd

DATA_DIR = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'

NEG_NOISE_MM = 25.4       # 1 inch: typical pillow-sensor baseline drift
MAX_PLAUSIBLE_MM = 3000.0  # ~118 in: well above the highest credible Sierra SWE


def qc(swe):
    swe = swe.copy()
    swe['qc_flag'] = 'ok'

    noise = swe['swe_mm'].between(-NEG_NOISE_MM, 0, inclusive='left')
    swe.loc[noise, 'swe_mm'] = 0.0
    swe.loc[noise, 'qc_flag'] = 'clipped'

    bad = (swe['swe_mm'] < -NEG_NOISE_MM) | (swe['swe_mm'] > MAX_PLAUSIBLE_MM)
    swe.loc[bad, 'swe_mm'] = pd.NA
    swe.loc[bad, 'qc_flag'] = 'dropped'

    return swe


def main():
    raw_csv = DATA_DIR + 'cdec_box_swe_wy1990-2026.csv'
    swe = pd.read_csv(raw_csv)
    print(f'{len(swe)} raw records <- {raw_csv}')

    swe = qc(swe)
    counts = swe['qc_flag'].value_counts()
    print(f'qc_flag counts: {counts.to_dict()}')

    qc_csv = DATA_DIR + 'cdec_box_swe_wy1990-2026_qc.csv'
    swe.to_csv(qc_csv, index=False)
    print(f'-> {qc_csv}')


if __name__ == '__main__':
    main()
