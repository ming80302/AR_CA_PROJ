#!/usr/bin/env python3
# Ming Ge / Claude, Oct 2026
#
# Extract daily-total precipitation (TP = large-scale + convective, in mm) and
# daily-total snowfall water-equivalent (SF, in mm) over the California
# bounding box, for January-May of a single year, from the ERA5 accumulated
# surface-forecast archive.
#
# ERA5 forecast-accumulated fields reset every 12 hours (inits at 06Z/18Z,
# each accumulating hourly for 12 steps). A calendar "day" here is therefore
# a 06Z-to-06Z(next day) window: value at forecast_hour=12 of the 06Z init
# (06Z-18Z) plus forecast_hour=12 of the 18Z init (18Z-06Z next day). This is
# the standard ECMWF accumulation-stitching convention for this production
# stream, not an arbitrary choice -- see get_precip_sf_ca test validation
# (box-mean precip drops to ~0 exactly during the independently-detected
# Jan 8-11 1990 Z500 ridging event).
#
# Usage:  python get_precip_sf_ca.py <year>
#
# Output: one NetCDF file per year with both variables on the CA box.

import os
import sys
import glob

import numpy as np
import pandas as pd
import xarray as xr

dir_era5 = '/glade/campaign/collections/rda/data/d633000/e5.oper.fc.sfc.accumu/'
dir_o = '/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking/'

# California bounding box (matches get_z500_t700_ca.py), longitudes in 0-360
LAT_S, LAT_N = 32.0, 42.5
LON_W, LON_E = 235.0, 246.0   # -125.0 to -114.0 deg E

MONTHS = [1, 2, 3, 4, 5]  # January - May
MONTH_NAMES = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May'}


def load_fhr12(year, month, varcode, varname):
    """Load forecast_hour=12 (12-hour accumulation total) over the CA box for
    every forecast_initial_time (06Z and 18Z) in a given year-month."""
    pattern = os.path.join(dir_era5, f'{year}{month:02d}', f'e5.oper.fc.sfc.accumu.{varcode}.ll025sc.*.nc')
    flnms = sorted(glob.glob(pattern))
    if not flnms:
        print(f'WARNING: no files found for {year}{month:02d} ({varcode})')
        return None
    das = []
    for f in flnms:
        with xr.open_dataset(f) as ds:
            da = ds[varname].sel(
                forecast_hour=12,
                latitude=slice(LAT_N, LAT_S),
                longitude=slice(LON_W, LON_E),
            ).load()
            das.append(da)
    return xr.concat(das, dim='forecast_initial_time').sortby('forecast_initial_time')


def daily_total(year, varcode, varname, out_name):
    """Sum the 06Z and 18Z 12-hour accumulations for each calendar day,
    across all of Jan-May for one year. Returns an (time, lat, lon) DataArray
    in mm, one value per complete calendar day."""
    month_das = [load_fhr12(year, m, varcode, varname) for m in MONTHS]
    month_das = [d for d in month_das if d is not None]
    da = xr.concat(month_das, dim='forecast_initial_time').sortby('forecast_initial_time')

    times = pd.to_datetime(da.forecast_initial_time.values)
    dates = times.normalize()
    vals = da.values * 1000.0  # m -> mm

    day_vals, day_dates = [], []
    df_dates = pd.Series(dates)
    for d, grp in df_dates.groupby(df_dates):
        idx = grp.index.values
        if len(idx) == 2:  # only keep calendar days with both the 06Z and 18Z accumulation present
            day_vals.append(vals[idx].sum(axis=0))
            day_dates.append(d)
        else:
            print(f'WARNING: {out_name} {d.date()} has {len(idx)} init(s), not 2 -- dropped')

    out = xr.DataArray(
        np.stack(day_vals), dims=('time', 'latitude', 'longitude'),
        coords={'time': pd.to_datetime(day_dates), 'latitude': da.latitude, 'longitude': da.longitude},
        name=out_name,
    )
    return out.sortby('time')


def main():
    year = int(sys.argv[1])
    flnm_o = os.path.join(dir_o, f'precip_sf_ca_{year}.nc')
    if os.path.isfile(flnm_o):
        print(flnm_o, 'already exists, skipping')
        return

    print(f'{year}: extracting large-scale + convective precip over CA box ...')
    lsp = daily_total(year, '128_142_lsp', 'LSP', 'lsp')
    cp = daily_total(year, '128_143_cp', 'CP', 'cp')
    tp = (lsp + cp).rename('tp')
    tp.attrs['units'] = 'mm'
    tp.attrs['description'] = 'daily-total precipitation (large-scale + convective) over CA box, 06Z-06Z day'

    print(f'{year}: extracting snowfall water-equivalent over CA box ...')
    sf = daily_total(year, '128_144_sf', 'SF', 'sf')
    sf.attrs['units'] = 'mm'
    sf.attrs['description'] = 'daily-total snowfall water-equivalent over CA box, 06Z-06Z day'

    ds_out = xr.merge([tp, sf])
    ds_out.attrs['script'] = 'get_precip_sf_ca.py'
    ds_out.attrs['box'] = f'lat {LAT_S}-{LAT_N}, lon {LON_W}-{LON_E} (California)'
    ds_out.attrs['months'] = '-'.join([MONTH_NAMES[MONTHS[0]], MONTH_NAMES[MONTHS[-1]]])
    ds_out.attrs['day_convention'] = '06Z to 06Z(next day), sum of two 12-hour ERA5 forecast accumulations'

    print(flnm_o)
    ds_out.to_netcdf(flnm_o)


if __name__ == '__main__':
    main()
