"""Shared climatology / event-detection helpers for the CA Z500-T700 blocking-ridge
and warm-anomaly notebooks (CA_z500_t700_methodA_vs_methodB.ipynb,
CA_z500_t700_methodC_5daymean_std.ipynb, and friends).

Pulling these into one module means a fix or change only has to be made once and is
picked up by every notebook that imports from here, instead of silently drifting
across copy-pasted cells.
"""

import numpy as np
import pandas as pd
from scipy.stats import linregress, theilslopes


# ---------------------------------------------------------------------------
# Climatology
# ---------------------------------------------------------------------------

def climatology_dict(time_index, vals, window=5, compute_std=True):
    """Per-calendar-day mean (and optionally std), pooling +/-window days across all
    years, keyed by (month, day). Works on any 1-D series passed in -- a series of
    daily values or a series of 5-day running means, whichever `vals` holds.

    Pools by sorted-(month, day) index proximity, so it does NOT handle a Dec->Jan
    wraparound -- it assumes `time_index` never spans both December and January.
    """
    time_index = pd.DatetimeIndex(time_index)
    months = set(time_index.month)
    if 12 in months and 1 in months:
        raise ValueError(
            'climatology_dict pools by sorted (month, day) index proximity and does '
            'not handle a Dec->Jan wraparound, but time_index spans both December '
            'and January. Restrict the input to a non-wrapping season first.'
        )

    md_key = list(zip(time_index.month, time_index.day))
    unique_keys = sorted(set(md_key))
    key_to_idx = {k: i for i, k in enumerate(unique_keys)}
    season_idx = np.array([key_to_idx[k] for k in md_key])
    clim_mean, clim_std = {}, {}
    for k, idx in key_to_idx.items():
        mask = (season_idx >= idx - window) & (season_idx <= idx + window)
        clim_mean[k] = vals[mask].mean(axis=0)
        if compute_std:
            clim_std[k] = vals[mask].std(axis=0)
    return (clim_mean, clim_std) if compute_std else clim_mean


def lookup_climatology(time_index, clim_dict):
    """Expand a (month, day) -> value dict into an array aligned to time_index."""
    time_index = pd.DatetimeIndex(time_index)
    md_key = list(zip(time_index.month, time_index.day))
    return np.array([clim_dict[k] for k in md_key])


def percentile_climatology(time_index, vals, window=5, percentiles=(90, 95, 99)):
    """Per-calendar-day empirical percentile(s), pooling +/-window days across all
    years -- an alternative to a parametric sigma threshold that makes no assumption
    about the tail shape of the pooled distribution (relevant here since CA Z500/T700
    anomalies are measurably skewed, not symmetric).
    """
    time_index = pd.DatetimeIndex(time_index)
    md_key = list(zip(time_index.month, time_index.day))
    unique_keys = sorted(set(md_key))
    key_to_idx = {k: i for i, k in enumerate(unique_keys)}
    season_idx = np.array([key_to_idx[k] for k in md_key])
    result = {p: {} for p in percentiles}
    for k, idx in key_to_idx.items():
        mask = (season_idx >= idx - window) & (season_idx <= idx + window)
        pooled = vals[mask]
        for p in percentiles:
            result[p][k] = np.percentile(pooled, p)
    return result


# ---------------------------------------------------------------------------
# Year-trend estimation and trend-consistent standardization
# ---------------------------------------------------------------------------

def fit_year_trend(residual, years, label='', method='theilsen', ci=90, verbose=True):
    """Fit a linear year-trend to the annual mean of `residual` (a climatology
    residual: value - flat climatological mean) and return (a) the fitted baseline
    shift for every row of `years`, and (b) a diagnostics dict.

    method='theilsen' (default) uses a robust, outlier-resistant slope estimator
    with a built-in confidence interval (scipy.stats.theilslopes) -- preferable to
    plain OLS here because annual Jan-Apr means are only 36 points and can carry
    low-frequency (e.g. decadal/ENSO-driven) autocorrelation that makes an OLS
    p-value overconfident. OLS is still fit and reported alongside for comparison.
    """
    annual_mean_residual = pd.Series(residual, index=years).groupby(level=0).mean()
    x = annual_mean_residual.index.values.astype(float)
    y = annual_mean_residual.values

    ols_slope, ols_intercept, r, p, se = linregress(x, y)
    info = {
        'method': method,
        'ols_slope_per_decade': ols_slope * 10,
        'ols_p': p,
        'ols_r': r,
    }

    if method == 'theilsen':
        ts_slope, ts_intercept, ts_lo, ts_hi = theilslopes(y, x, alpha=ci / 100)
        slope, intercept = ts_slope, ts_intercept
        info.update(slope_per_decade=slope * 10, ci_lo_per_decade=ts_lo * 10,
                    ci_hi_per_decade=ts_hi * 10, ci_pct=ci)
        if verbose:
            print(f'{label}: Theil-Sen trend = {slope * 10:+.3f}/decade '
                  f'({ci:.0f}% CI [{ts_lo * 10:+.3f}, {ts_hi * 10:+.3f}]/decade); '
                  f'OLS = {ols_slope * 10:+.3f}/decade (p={p:.3f}, r={r:.2f})')
    elif method == 'ols':
        slope, intercept = ols_slope, ols_intercept
        info.update(slope_per_decade=slope * 10)
        if verbose:
            print(f'{label}: OLS trend = {slope * 10:+.3f}/decade (p={p:.3f}, r={r:.2f})')
    else:
        raise ValueError(f"method must be 'theilsen' or 'ols', got {method!r}")

    trend_lookup = intercept + slope * years
    return trend_lookup, info


def standardize_with_trend(time_index, vals, window=5, label='', trend_method='theilsen', verbose=True):
    """Year-detrended standardized anomaly, with the climatological mean AND standard
    deviation estimated consistently from the SAME (detrended) baseline.

    The naive approach -- pool raw values for clim_mean and clim_std, then only
    shift clim_mean by a fitted trend -- leaves clim_std computed as the dispersion
    of raw, trend-contaminated values around a flat mean, while the numerator has
    already had the trend removed. That mismatch inflates the standard deviation
    used to normalize anomalies by however much of the pooled variance is actually
    secular drift rather than year-to-year synoptic variability.

    This function instead: (1) estimates a flat per-calendar-day climatological
    mean, (2) fits the year-trend on the residual from that flat mean, (3) removes
    the trend from the raw values, (4) re-pools the now-detrended values to get a
    climatological mean AND std that are both computed on the same detrended basis.

    Returns (sanom, diagnostics) where diagnostics also reports the "naive" (trend-
    contaminated) std alongside the corrected one, so the size of the fix is visible
    rather than silently applied.
    """
    time_index = pd.DatetimeIndex(time_index)
    years = time_index.year.values

    clim_mean0 = climatology_dict(time_index, vals, window=window, compute_std=False)
    m0 = lookup_climatology(time_index, clim_mean0)
    residual0 = vals - m0

    trend_lookup, trend_info = fit_year_trend(residual0, years, label=label, method=trend_method, verbose=verbose)
    detrended_vals = vals - trend_lookup

    clim_mean, clim_std = climatology_dict(time_index, detrended_vals, window=window, compute_std=True)
    m = lookup_climatology(time_index, clim_mean)
    s = lookup_climatology(time_index, clim_std)
    sanom = (detrended_vals - m) / s

    # naive (pre-fix) std, for comparison/reporting only -- not used in sanom above
    _, clim_std_raw = climatology_dict(time_index, vals, window=window, compute_std=True)
    s_raw = lookup_climatology(time_index, clim_std_raw)

    pct_diff = 100 * (1 - s.mean() / s_raw.mean())
    if verbose:
        print(f'{label}: clim_std, naive (trend-contaminated) = {s_raw.mean():.4f}, '
              f'detrended (corrected) = {s.mean():.4f} ({pct_diff:+.3f}% difference)')

    diagnostics = {
        'trend': trend_info,
        'trend_lookup': trend_lookup,
        'clim_mean': m,
        'clim_std': s,
        'clim_std_raw': s_raw,
        'detrended_vals': detrended_vals,
    }
    return sanom, diagnostics


# ---------------------------------------------------------------------------
# Rolling means
# ---------------------------------------------------------------------------

def rolling_mean_per_year(series, window):
    """Centered rolling mean computed independently within each year's block, so the
    window never bridges a real year-boundary gap in the record (e.g. Apr->Jan).
    """
    return series.groupby(series.index.year).transform(
        lambda g: g.rolling(window, center=True).mean()
    )


# ---------------------------------------------------------------------------
# Event (cluster) detection
# ---------------------------------------------------------------------------

def _segment_ids(dates):
    """Integer segment id per row, incrementing wherever consecutive dates aren't
    exactly 1 calendar day apart -- used so clustering never bridges a real gap
    (e.g. the Apr->Jan year boundary) in an otherwise daily record.
    """
    n = len(dates)
    seg_id = np.zeros(n, dtype=int)
    for i in range(1, n):
        seg_id[i] = seg_id[i - 1] + (1 if (dates[i] - dates[i - 1]).days != 1 else 0)
    return seg_id


def _merged_runs(seg_id, exceed, max_gap):
    """(start_idx, end_idx) absolute-position tuples for exceedance runs, merging
    runs separated by at most `max_gap` sub-threshold days -- but never merging
    across a segment boundary from `_segment_ids`.
    """
    clusters = []
    for seg in np.unique(seg_id):
        idx = np.where(seg_id == seg)[0]
        seg_exceed = exceed[idx]
        runs = []
        start = None
        for j, val in enumerate(seg_exceed):
            if val and start is None:
                start = j
            elif not val and start is not None:
                runs.append((start, j - 1))
                start = None
        if start is not None:
            runs.append((start, len(seg_exceed) - 1))

        merged = []
        for run in runs:
            if merged and run[0] - merged[-1][1] - 1 <= max_gap:
                merged[-1] = (merged[-1][0], run[1])
            else:
                merged.append(list(run))

        for js, je in merged:
            clusters.append((idx[js], idx[je]))
    return clusters


def find_events(dates, sanom, threshold, min_duration, sign=1, max_gap=1):
    """Group calendar days where sign*sanom >= threshold into events, tolerating
    short sub-threshold dips (up to max_gap calendar days) within an otherwise
    persistent run.

    Each event record includes `second_peak_sanom` (the second-highest value within
    the event) alongside `peak_sanom` -- ranking by a single maximum is subject to
    selection bias (an event's peak is, by construction, the largest of several
    noisy daily/5-day values, so top-ranked peaks are optimistically biased); seeing
    peak and second-peak together makes it visible whether an event's extremity is a
    single-point spike or a genuinely sustained plateau.
    """
    exceed = (sign * sanom) >= threshold
    seg_id = _segment_ids(dates)
    clusters = _merged_runs(seg_id, exceed, max_gap)

    records = []
    for s, e in clusters:
        duration = e - s + 1
        if duration >= min_duration:
            seg_sanom = sign * sanom[s:e + 1]
            sorted_vals = np.sort(seg_sanom)
            records.append({
                'start_date': dates[s].date(),
                'end_date': dates[e].date(),
                'duration_days': duration,
                'n_gap_days': int((~exceed[s:e + 1]).sum()),
                'peak_sanom': sorted_vals[-1],
                'second_peak_sanom': sorted_vals[-2] if sorted_vals.size > 1 else sorted_vals[-1],
                'mean_sanom': seg_sanom.mean(),
            })
    return pd.DataFrame(records)


def extremal_index_runs(dates, exceed_bool, max_gaps=(0, 1, 2, 3)):
    """Runs-estimator of the extremal index theta = n_clusters / n_exceedance_days
    for a range of declustering gap tolerances -- lets a MAX_GAP choice be justified
    empirically (the gap at which theta stabilizes / implied cluster length matches
    the phenomenon of interest) rather than asserted as a fixed constant.
    """
    seg_id = _segment_ids(dates)
    n_exceed = int(exceed_bool.sum())
    rows = []
    for gap in max_gaps:
        n_clusters = len(_merged_runs(seg_id, exceed_bool, gap))
        theta = n_clusters / n_exceed if n_exceed else np.nan
        rows.append({
            'max_gap': gap,
            'n_exceedance_days': n_exceed,
            'n_clusters': n_clusters,
            'extremal_index_theta': theta,
            'implied_mean_cluster_length': (1 / theta) if theta else np.nan,
        })
    return pd.DataFrame(rows)


def match_rate(left, right, label_left, label_right):
    """For each (variable, threshold_sd) group, count how many `left` events have an
    overlapping `right` event (date-range intersection), vectorized via a pairwise
    ordinal-date comparison matrix instead of a nested .iterrows() loop.
    """
    rows = []
    for (var, thr), lgrp in left.groupby(['variable', 'threshold_sd']):
        rgrp = right[(right.variable == var) & (right.threshold_sd == thr)]
        if len(rgrp) == 0:
            n_matched = 0
        else:
            l_start = np.array([d.toordinal() for d in lgrp['start_date']])
            l_end = np.array([d.toordinal() for d in lgrp['end_date']])
            r_start = np.array([d.toordinal() for d in rgrp['start_date']])
            r_end = np.array([d.toordinal() for d in rgrp['end_date']])
            overlap = (l_start[:, None] <= r_end[None, :]) & (r_start[None, :] <= l_end[:, None])
            n_matched = int(overlap.any(axis=1).sum())
        rows.append({'variable': var, 'threshold_sd': thr,
                     f'n_{label_left}': len(lgrp), f'matched_by_{label_right}': n_matched})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Bootstrap uncertainty
# ---------------------------------------------------------------------------

def bootstrap_climatology_std(time_index, vals, window=5, n_boot=200, ci=90, random_state=0):
    """Year-block bootstrap confidence interval for the calendar-day-averaged
    climatological standard deviation. Resamples the set of years with replacement;
    since `climatology_dict` only keys on (month, day), a repeated year can be
    represented by simply repeating its rows via fancy indexing -- no special
    handling needed to keep the pooling logic correct under resampling.

    Returns (bootstrap_replicates, (ci_lo, ci_hi)).
    """
    time_index = pd.DatetimeIndex(time_index)
    years = time_index.year.values
    uniq_years = np.unique(years)
    rng = np.random.default_rng(random_state)

    year_row_idx = {y: np.where(years == y)[0] for y in uniq_years}
    boot_stats = np.empty(n_boot)
    for b in range(n_boot):
        draw = rng.choice(uniq_years, size=len(uniq_years), replace=True)
        idx = np.concatenate([year_row_idx[y] for y in draw])
        _, clim_std_b = climatology_dict(time_index[idx], vals[idx], window=window, compute_std=True)
        boot_stats[b] = np.mean(list(clim_std_b.values()))

    lo = np.percentile(boot_stats, (100 - ci) / 2)
    hi = np.percentile(boot_stats, 100 - (100 - ci) / 2)
    return boot_stats, (lo, hi)


# ---------------------------------------------------------------------------
# Lightweight self-tests (run with `python ca_blocking_lib.py`, no pytest needed)
# ---------------------------------------------------------------------------

def _self_test():
    rng = np.random.default_rng(0)

    # climatology_dict: pooled std should shrink the closer vals are to constant
    dates = pd.date_range('2000-01-01', '2000-04-30')
    time_index = pd.DatetimeIndex(np.tile(dates.values, 10))
    vals = rng.normal(0, 1, len(time_index))
    clim_mean, clim_std = climatology_dict(time_index, vals, window=5)
    assert set(clim_mean.keys()) == set(clim_std.keys())
    assert all(s >= 0 for s in clim_std.values())

    # wraparound guard must reject a Dec->Jan span
    bad_index = pd.date_range('2000-12-01', '2001-01-31')
    try:
        climatology_dict(bad_index, np.zeros(len(bad_index)))
        raise AssertionError('expected ValueError for Dec->Jan wraparound input')
    except ValueError:
        pass

    # standardize_with_trend: a known year-trend plus Gaussian noise (no seasonal
    # cycle, so climatology pooling doesn't itself add dispersion) should recover
    # ~the true slope, and the resulting sanom should be well-behaved (finite,
    # roughly standardized) rather than blowing up
    trend_dates = pd.DatetimeIndex(np.concatenate(
        [pd.date_range(f'{y}-01-01', f'{y}-04-30').values for y in range(1990, 2010)]
    ))
    trend_years = trend_dates.year.values
    true_slope_per_year = 2.0
    trend_vals = (trend_years - 1990) * true_slope_per_year + rng.normal(0, 5.0, len(trend_dates))
    sanom, diag = standardize_with_trend(trend_dates, trend_vals, window=5, label='_self_test', trend_method='theilsen')
    fitted_slope_per_decade = diag['trend']['slope_per_decade']
    assert abs(fitted_slope_per_decade - true_slope_per_year * 10) < 5, (
        f'expected ~{true_slope_per_year * 10}/decade, got {fitted_slope_per_decade:.2f}/decade'
    )
    assert np.isfinite(sanom).all(), 'sanom should be finite everywhere'
    assert 0.5 < sanom.std() < 2.0, f'standardized anomaly should have std near 1, got {sanom.std():.3f}'

    # find_events: a single isolated 5-day spike should be found once, and merge
    # across a 1-day dip but not a 2-day dip
    n = 20
    sig = np.zeros(n)
    sig[5:10] = 2.0
    ev = find_events(dates[:n], sig, threshold=1, min_duration=1, sign=1, max_gap=1)
    assert len(ev) == 1 and ev.iloc[0]['duration_days'] == 5

    sig_gap1 = sig.copy()
    sig_gap1[7] = 0.0  # 1-day dip inside the run
    ev_gap1 = find_events(dates[:n], sig_gap1, threshold=1, min_duration=1, sign=1, max_gap=1)
    assert len(ev_gap1) == 1, 'a 1-day dip should merge into one event when max_gap=1'

    sig_gap2 = sig.copy()
    sig_gap2[7:9] = 0.0  # 2-day dip inside the run
    ev_gap2 = find_events(dates[:n], sig_gap2, threshold=1, min_duration=1, sign=1, max_gap=1)
    assert len(ev_gap2) == 2, 'a 2-day dip should NOT merge into one event when max_gap=1'

    # second_peak_sanom should never exceed peak_sanom
    assert (ev['second_peak_sanom'] <= ev['peak_sanom']).all()

    # extremal_index_runs: theta should be in (0, 1] and monotonically non-increasing
    # as max_gap grows (more merging -> fewer, not more, clusters)
    exceed = sig > 1
    ext = extremal_index_runs(dates[:n], exceed, max_gaps=(0, 1, 2))
    assert ext['extremal_index_theta'].between(0, 1, inclusive='right').all()
    assert (ext['n_clusters'].diff().dropna() <= 0).all()

    # match_rate: an event fully contained in another's window should match
    left = pd.DataFrame({'variable': ['x'], 'threshold_sd': [1],
                          'start_date': [dates[5].date()], 'end_date': [dates[9].date()]})
    right = pd.DataFrame({'variable': ['x'], 'threshold_sd': [1],
                           'start_date': [dates[6].date()], 'end_date': [dates[7].date()]})
    mr = match_rate(left, right, 'left', 'right')
    assert mr.loc[0, 'matched_by_right'] == 1

    # bootstrap_climatology_std: CI should bracket the point estimate and be ordered
    boot, (lo, hi) = bootstrap_climatology_std(time_index, vals, window=5, n_boot=50, random_state=1)
    assert lo <= np.median(boot) <= hi

    # percentile_climatology: 99th percentile should be >= 90th for every calendar day
    pct = percentile_climatology(time_index, vals, window=5, percentiles=(90, 99))
    assert all(pct[99][k] >= pct[90][k] for k in pct[90])

    print('ca_blocking_lib: all self-tests passed')


if __name__ == '__main__':
    _self_test()
