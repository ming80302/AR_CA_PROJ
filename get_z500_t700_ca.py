#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Extract daily-mean 500 hPa geopotential height (Z500, in meters) and
# 700 hPa temperature (T700, in K) over a California bounding box,
# for January-April of a single year, from the ERA5 pressure-level archive.
#
# Usage:  python get_z500_t700_ca.py <year>
#
# Output: one NetCDF file per year with both variables already averaged
# onto a small CA box, small enough for the analysis notebook to load
# directly (no need to touch the multi-TB raw archive again).

import os
import sys
import glob
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
import xarray as xr

G = 9.80665  # m/s^2, used to convert geopotential -> geopotential height

dir_era5 = '/glade/campaign/collections/rda/data/d633000/e5.oper.an.pl/'
dir_o = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'

# California bounding box (with a small buffer), longitudes in 0-360
LAT_S, LAT_N = 32.0, 42.5
LON_W, LON_E = 235.0, 246.0   # -125.0 to -114.0 deg E

MONTHS = [1, 2, 3, 4]  # January - April


def read_one_day(args):
    flnm, varname, level = args
    with xr.open_dataset(flnm) as ds:
        da = ds[varname].sel(
            level=level,
            latitude=slice(LAT_N, LAT_S),
            longitude=slice(LON_W, LON_E),
        ).mean(dim='time').load()
    # drop the scalar 'level' coord so Z500 (level=500) and T700 (level=700)
    # don't conflict when later merged into one Dataset
    return da.drop_vars('level')


def extract_var(year, varcode, varname, level, out_level_name):
    """varcode e.g. '128_129_z', varname e.g. 'Z'."""
    day_das = []
    day_strs = []
    for month in MONTHS:
        yyyymm = f'{year}{month:02d}'
        pattern = os.path.join(dir_era5, yyyymm, f'e5.oper.an.pl.{varcode}.ll025sc.*.nc')
        flnms = sorted(glob.glob(pattern))
        if not flnms:
            print(f'WARNING: no files found for {yyyymm} ({varcode})')
            continue
        tasks = [(f, varname, level) for f in flnms]
        with ProcessPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(read_one_day, tasks))
        for flnm, da in zip(flnms, results):
            # file name encodes the day, e.g. ...1990010100_1990010123.nc
            yyyymmdd = os.path.basename(flnm).split('.')[-2].split('_')[0][:8]
            day_das.append(da)
            day_strs.append(yyyymmdd)

    time_index = pd.to_datetime(day_strs, format='%Y%m%d')
    out = xr.concat(day_das, dim='time')
    out = out.assign_coords(time=time_index).sortby('time')
    out = out.rename(out_level_name)
    return out


def main():
    year = int(sys.argv[1])
    flnm_o = os.path.join(dir_o, f'z500_t700_ca_{year}.nc')
    if os.path.isfile(flnm_o):
        print(flnm_o, 'already exists, skipping')
        return

    print(f'{year}: extracting Z500 over CA box ...')
    z500 = extract_var(year, '128_129_z', 'Z', 500.0, 'z500')
    z500 = z500 / G  # geopotential -> geopotential height (m)
    z500.attrs['units'] = 'm'
    z500.attrs['description'] = 'daily-mean 500 hPa geopotential height over CA box'

    print(f'{year}: extracting T700 over CA box ...')
    t700 = extract_var(year, '128_130_t', 'T', 700.0, 't700')
    t700.attrs['units'] = 'K'
    t700.attrs['description'] = 'daily-mean 700 hPa temperature over CA box'

    ds_out = xr.merge([z500, t700])
    ds_out.attrs['script'] = 'get_z500_t700_ca.py'
    ds_out.attrs['box'] = f'lat {LAT_S}-{LAT_N}, lon {LON_W}-{LON_E} (California)'
    ds_out.attrs['months'] = 'Jan-Apr'

    print(flnm_o)
    ds_out.to_netcdf(flnm_o)


if __name__ == '__main__':
    main()
