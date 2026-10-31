#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Extract upstream Pacific-basin fields relevant to what lets a California
# ridge/warm-spell "heat wave" persist -- 300 hPa height and wind (jet stream /
# Rossby wave pattern), surface MSLP, SST, total cloud cover, and IVT
# components (vertically-integrated water vapor flux) -- for a single year,
# Jan-Apr, over a wide Pacific-North America domain.
#
# Companion to get_z500_t700_ca.py, which only covers the small CA box and so
# cannot say anything about *why* a ridge forms or persists. This script is
# the first step toward the upstream-mechanism question raised when reviewing
# CA_z500_t700_blocking_events_detrend_5day.ipynb's Section 8 (2026
# out-of-sample test): does the record March 2026 episode (Z500 2.72 sigma,
# T700 3.09 sigma, 19 days -- the longest/strongest in the 1990-2025 record)
# show an omega-block / weakened-jet signature that the three shorter,
# ordinary-strength WY2026 episodes (Jan 10-18, Jan 29-Feb 5, Feb 23-Mar 1) do
# not?
#
# Usage:  python get_upstream_pacific.py <year>
#
# Output: one NetCDF file per year with all eight fields on a common daily
# time axis, over the Pacific-North America domain below.

import os
import sys
import glob
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
import xarray as xr

G = 9.80665  # m/s^2, geopotential -> geopotential height

dir_pl = '/glade/campaign/collections/rda/data/d633000/e5.oper.an.pl/'
dir_sfc = '/glade/campaign/collections/rda/data/d633000/e5.oper.an.sfc/'
dir_vinteg = '/glade/campaign/collections/rda/data/d633000/e5.oper.an.vinteg/'
dir_o = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'

# Pacific-North America domain -- wide enough to see an omega-block's flanking
# troughs (one upstream over the N Pacific/Gulf of Alaska, one downstream over
# the Rockies) around a CA ridge, not just the ridge itself.
LAT_S, LAT_N = 15.0, 65.0
LON_W, LON_E = 140.0, 250.0   # 140E, across the dateline, to -110E (Rockies)

MONTHS = [1, 2, 3, 4]  # January - April, matches get_z500_t700_ca.py


def read_one_pl_day(args):
    flnm, varname, level = args
    with xr.open_dataset(flnm, engine='netcdf4') as ds:
        da = ds[varname].sel(
            level=level,
            latitude=slice(LAT_N, LAT_S),
            longitude=slice(LON_W, LON_E),
        ).mean(dim='time').load()
    # drop the scalar 'level' coord so z300/u300/v300 don't conflict on merge
    return da.drop_vars('level')


def extract_pl_var(year, varcode, grid, varname, level, out_name):
    """Pressure-level analysis field, one file per day. `grid` is 'sc'
    (scalar, e.g. Z) or 'uv' (vector components, e.g. U/V) -- RDA stores them
    under different filename tags even though both sit on the same regular
    0.25-deg grid."""
    day_das, day_strs = [], []
    for month in MONTHS:
        yyyymm = f'{year}{month:02d}'
        pattern = os.path.join(dir_pl, yyyymm, f'e5.oper.an.pl.{varcode}.ll025{grid}.*.nc')
        flnms = sorted(glob.glob(pattern))
        if not flnms:
            print(f'WARNING: no files found for {yyyymm} ({varcode})')
            continue
        tasks = [(f, varname, level) for f in flnms]
        with ProcessPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(read_one_pl_day, tasks))
        for flnm, da in zip(flnms, results):
            # file name encodes the day, e.g. ...2026030100_2026030123.nc
            yyyymmdd = os.path.basename(flnm).split('.')[-2].split('_')[0][:8]
            day_das.append(da)
            day_strs.append(yyyymmdd)

    time_index = pd.to_datetime(day_strs, format='%Y%m%d')
    out = xr.concat(day_das, dim='time').assign_coords(time=time_index).sortby('time')
    return out.rename(out_name)


def extract_monthly_var(dir_product, product_tag, year, varcode, varname, out_name):
    """Surface or vertically-integrated analysis field -- RDA stores these as
    one file per *month* (not per day), so just open each month's file,
    subset the domain, and resample hourly -> daily mean directly."""
    month_das = []
    for month in MONTHS:
        yyyymm = f'{year}{month:02d}'
        pattern = os.path.join(dir_product, yyyymm, f'{product_tag}.{varcode}.ll025sc.*.nc')
        flnms = sorted(glob.glob(pattern))
        if not flnms:
            print(f'WARNING: no files found for {yyyymm} ({varcode})')
            continue
        with xr.open_dataset(flnms[0], engine='netcdf4') as ds:
            da = ds[varname].sel(
                latitude=slice(LAT_N, LAT_S),
                longitude=slice(LON_W, LON_E),
            ).load()
        month_das.append(da.resample(time='1D').mean())
    out = xr.concat(month_das, dim='time').sortby('time')
    return out.rename(out_name)


def main():
    year = int(sys.argv[1])
    flnm_o = os.path.join(dir_o, f'upstream_pacific_{year}.nc')
    if os.path.isfile(flnm_o):
        print(flnm_o, 'already exists, skipping')
        return

    print(f'{year}: extracting Z300 over the Pacific-N America domain ...')
    z300 = extract_pl_var(year, '128_129_z', 'sc', 'Z', 300.0, 'z300') / G
    z300.attrs.update(units='m', description='daily-mean 300 hPa geopotential height')

    print(f'{year}: extracting U300/V300 ...')
    u300 = extract_pl_var(year, '128_131_u', 'uv', 'U', 300.0, 'u300')
    u300.attrs.update(units='m/s', description='daily-mean 300 hPa zonal wind')
    v300 = extract_pl_var(year, '128_132_v', 'uv', 'V', 300.0, 'v300')
    v300.attrs.update(units='m/s', description='daily-mean 300 hPa meridional wind')

    print(f'{year}: extracting surface MSLP, SST, cloud cover ...')
    msl = extract_monthly_var(dir_sfc, 'e5.oper.an.sfc', year, '128_151_msl', 'MSL', 'msl') / 100.0
    msl.attrs.update(units='hPa', description='daily-mean mean sea level pressure')
    sst = extract_monthly_var(dir_sfc, 'e5.oper.an.sfc', year, '128_034_sstk', 'SSTK', 'sst') - 273.15
    sst.attrs.update(units='degC', description='daily-mean sea surface temperature (NaN over land)')
    tcc = extract_monthly_var(dir_sfc, 'e5.oper.an.sfc', year, '128_164_tcc', 'TCC', 'tcc')
    tcc.attrs.update(units='0-1', description='daily-mean total cloud cover fraction')

    print(f'{year}: extracting IVT components ...')
    viwve = extract_monthly_var(dir_vinteg, 'e5.oper.an.vinteg', year, '162_071_viwve', 'VIWVE', 'viwve')
    viwve.attrs.update(units='kg m**-1 s**-1',
                        description='daily-mean vertical integral of eastward water vapour flux')
    viwvn = extract_monthly_var(dir_vinteg, 'e5.oper.an.vinteg', year, '162_072_viwvn', 'VIWVN', 'viwvn')
    viwvn.attrs.update(units='kg m**-1 s**-1',
                        description='daily-mean vertical integral of northward water vapour flux')

    ds_out = xr.merge([z300, u300, v300, msl, sst, tcc, viwve, viwvn])
    ds_out.attrs['script'] = 'get_upstream_pacific.py'
    ds_out.attrs['box'] = f'lat {LAT_S}-{LAT_N}, lon {LON_W}-{LON_E} (Pacific-North America)'
    ds_out.attrs['months'] = 'Jan-Apr'

    print(flnm_o)
    ds_out.to_netcdf(flnm_o)


if __name__ == '__main__':
    main()
