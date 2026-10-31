#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Extract potential vorticity (PV), temperature, and horizontal wind (U, V) at a
# vertical-level bracket spanning the dynamic tropopause (2 PVU surface), over the
# same Pacific-North America domain as get_upstream_pacific.py, for a single year,
# Jan-Apr.
#
# This is the data needed to reproduce the dynamic-tropopause (DT) diagnostics in
# "The Anti-AR of March 2026" (Chris Davis, UMass Amherst/NCAR, June 2026,
# ~/ERA5/March_2026_Western-US-Heat Wave.pdf): theta-on-DT maps and DT Hovmoller
# diagrams (meridional wind and theta deviation from zonal mean). A single
# fixed-pressure-level composite (get_upstream_pacific.py's Z300/U300/V300) can't
# resolve this, since the actual 2-PVU surface sits at very different pressures in
# the subtropics vs. under an anomalously amplified ridge -- that paper's own
# finding is that the dynamic tropopause "remains very high" (low pressure) under
# the ridge, which a fixed-300-hPa view would never show.
#
# Usage:  python get_upstream_pv_theta.py <year>
#
# Output: one NetCDF per year with PV, T, U, V on (time, level, latitude,
# longitude), level = [500,400,300,250,200,175,150,125,100,70,50] hPa (descending
# pressure / ascending altitude order, for the DT-crossing search).

import os
import sys
import glob
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
import xarray as xr

dir_pl = '/glade/campaign/collections/rda/data/d633000/e5.oper.an.pl/'
dir_o = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'

LAT_S, LAT_N = 15.0, 65.0
LON_W, LON_E = 140.0, 250.0

# Descending pressure (ascending altitude) -- the order the DT-crossing search
# (built in the analysis notebook) walks upward from. 50 hPa included as a safety
# margin above 70, since the ridge's dynamic tropopause can sit anomalously high.
LEVELS = [500.0, 400.0, 300.0, 250.0, 200.0, 175.0, 150.0, 125.0, 100.0, 70.0, 50.0]
MONTHS = [1, 2, 3, 4]


def read_one_pl_day(args):
    flnm, varname = args
    with xr.open_dataset(flnm, engine='netcdf4') as ds:
        da = ds[varname].sel(
            level=LEVELS,
            latitude=slice(LAT_N, LAT_S),
            longitude=slice(LON_W, LON_E),
        ).mean(dim='time').load()
    return da


def extract_pl_var(year, varcode, grid, varname, out_name):
    """Pressure-level analysis field, one file per day, all LEVELS kept (not
    reduced to one) -- grid is 'sc' (scalar, PV/T) or 'uv' (vector, U/V)."""
    day_das, day_strs = [], []
    for month in MONTHS:
        yyyymm = f'{year}{month:02d}'
        pattern = os.path.join(dir_pl, yyyymm, f'e5.oper.an.pl.{varcode}.ll025{grid}.*.nc')
        flnms = sorted(glob.glob(pattern))
        if not flnms:
            print(f'WARNING: no files found for {yyyymm} ({varcode})')
            continue
        tasks = [(f, varname) for f in flnms]
        with ProcessPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(read_one_pl_day, tasks))
        for flnm, da in zip(flnms, results):
            yyyymmdd = os.path.basename(flnm).split('.')[-2].split('_')[0][:8]
            day_das.append(da)
            day_strs.append(yyyymmdd)

    time_index = pd.to_datetime(day_strs, format='%Y%m%d')
    out = xr.concat(day_das, dim='time').assign_coords(time=time_index).sortby('time')
    return out.rename(out_name)


def main():
    year = int(sys.argv[1])
    flnm_o = os.path.join(dir_o, f'upstream_pv_theta_{year}.nc')
    if os.path.isfile(flnm_o):
        print(flnm_o, 'already exists, skipping')
        return

    print(f'{year}: extracting PV ...')
    pv = extract_pl_var(year, '128_060_pv', 'sc', 'PV', 'pv')
    pv.attrs.update(units='K m**2 kg**-1 s**-1', description='daily-mean potential vorticity')

    print(f'{year}: extracting T ...')
    t = extract_pl_var(year, '128_130_t', 'sc', 'T', 't')
    t.attrs.update(units='K', description='daily-mean temperature')

    print(f'{year}: extracting U ...')
    u = extract_pl_var(year, '128_131_u', 'uv', 'U', 'u')
    u.attrs.update(units='m/s', description='daily-mean zonal wind')

    print(f'{year}: extracting V ...')
    v = extract_pl_var(year, '128_132_v', 'uv', 'V', 'v')
    v.attrs.update(units='m/s', description='daily-mean meridional wind')

    ds_out = xr.merge([pv, t, u, v])
    ds_out.attrs['script'] = 'get_upstream_pv_theta.py'
    ds_out.attrs['box'] = f'lat {LAT_S}-{LAT_N}, lon {LON_W}-{LON_E} (Pacific-North America)'
    ds_out.attrs['levels_hPa'] = str(LEVELS)
    ds_out.attrs['months'] = 'Jan-Apr'

    print(flnm_o)
    ds_out.to_netcdf(flnm_o)


if __name__ == '__main__':
    main()
