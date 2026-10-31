#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Extract daily-mean 2m air temperature (K), cosine-latitude-weighted box average
# over the Sierra sub-box (same bounds as CA_snowmelt_events_detrend_5day.ipynb's
# SIERRA_LAT_S/LAT_N/LON_W/LON_E), for January-April of a single year, from the
# ERA5 surface analysis archive.
#
# Built to replicate the local-temperature heatwave definition used in Guo and He
# (2026, Environ. Res. Lett. 21 194013, "Heatwaves drive rapid snowmelt and disrupt
# streamflow in the western United States") -- a per-location quantile exceedance
# of air temperature, as a box-averaged analog -- rather than this project's own
# synoptic Z500/T700 ridging definition, to test whether a simpler local-warmth
# definition matches the Sierra rapid-decline melt events differently, particularly
# in April (see CA_snowmelt_april_vs_janmar_match_test.ipynb's discussion of Guo and
# He's reduced-cold-content mechanism).
#
# Usage:  python get_t2m_sierra.py <year>
#
# Output: one NetCDF file per year with daily-mean T2M box-averaged over the
# Sierra sub-box.

import os
import sys
import glob

import numpy as np
import pandas as pd
import xarray as xr

dir_era5 = '/glade/campaign/collections/rda/data/d633000/e5.oper.an.sfc/'
dir_o = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'

# Sierra sub-box, matching CA_snowmelt_events_detrend_5day.ipynb's station-filtering
# box exactly (longitudes in 0-360 here: -121.0/-116.5 -> 239.0/243.5)
LAT_S, LAT_N = 34.5, 40.0
LON_W, LON_E = 239.0, 243.5

MONTHS = [1, 2, 3, 4]


def main():
    year = int(sys.argv[1])
    flnm_o = os.path.join(dir_o, f't2m_sierra_{year}.nc')
    if os.path.isfile(flnm_o):
        print(flnm_o, 'already exists, skipping')
        return

    month_das = []
    for month in MONTHS:
        yyyymm = f'{year}{month:02d}'
        pattern = os.path.join(dir_era5, yyyymm, 'e5.oper.an.sfc.128_167_2t.ll025sc.*.nc')
        flnms = sorted(glob.glob(pattern))
        if not flnms:
            print(f'WARNING: no files found for {yyyymm}')
            continue
        with xr.open_dataset(flnms[0], engine='netcdf4') as ds:
            da = ds.VAR_2T.sel(
                latitude=slice(LAT_N, LAT_S),
                longitude=slice(LON_W, LON_E),
            ).load()
        weights = np.cos(np.deg2rad(da.latitude))
        da_box = da.weighted(weights).mean(dim=('latitude', 'longitude'))
        month_das.append(da_box.resample(time='1D').mean())

    out = xr.concat(month_das, dim='time').sortby('time').rename('t2m')
    out.attrs['units'] = 'K'
    out.attrs['description'] = 'daily-mean 2m air temperature, Sierra-box cosine-weighted average'
    out.attrs['script'] = 'get_t2m_sierra.py'
    out.attrs['box'] = f'lat {LAT_S}-{LAT_N}, lon {LON_W}-{LON_E} (Sierra, matches snowmelt notebook)'
    out.attrs['months'] = 'Jan-Apr'

    print(flnm_o)
    out.to_netcdf(flnm_o)


if __name__ == '__main__':
    main()
