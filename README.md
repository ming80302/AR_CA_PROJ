# AR/CA snowpack-heatwave project

**Status: ongoing, exploratory work.** Methodology, parameter choices, and even
headline event counts have changed multiple times as stress-testing has turned up
issues (see `proj_note.ipynb`); treat anything here as current best understanding,
not a finished result.

Use ERA5 to identify late-season heat waves over the West Coast: periods marked by
both a pronounced atmospheric anomaly -- high-amplitude ridging or a blocking
anticyclone -- and high temperatures in the lower troposphere, occurring late enough
in the winter that there isn't much chance to make up the resulting snow loss before
the full onset of spring. Find all such ridging/blocking-and-warm periods, find
periods of unusually rapid snow decrease, and explore the relationship between them.

Two halves of one question, covered by two notebook families that share a data period
(water years 1990-2025 fit, 2026 held out and scored out-of-sample) and a common
analysis pattern (detrended calendar-day climatology, gap-tolerant multi-day
persistence rule, bootstrap CIs).

See `proj_note.ipynb` for the running, dated log of decisions, findings, and
follow-ups -- it's the most detailed record of *why* things are the way they are.
This README is an orientation map, not a substitute for it.

## Atmospheric side: Z500 ridging / T700 warm-spell detection

- **`CA_z500_t700_blocking_events_detrend_5day.ipynb`** -- the headline notebook.
  Box-mean Z500/T700 over California, Jan-Apr, standardized against a detrended
  +/-5-day pooled calendar-day climatology (fit on 1990-2025, 2026 held out), events =
  >=5 consecutive days at/above 1/2/3 sigma.
- **`CA_z500_t700_blocking_events_detrend_3day.ipynb`** /
  **`CA_z500_t700_blocking_events_mindur_comparison.ipynb`** -- `MIN_DURATION`
  sensitivity (3-day vs. 5-day persistence threshold).
- **`CA_z500_t700_methodA_vs_methodB.ipynb`** -- average-then-standardize vs.
  standardize-then-average, tests whether per-point variability differences change
  which events get flagged.
- **`CA_z500_t700_methodC_5daymean_std.ipynb`** -- alternative event definition using
  the standard deviation of the distribution of 5-day means, instead of the
  consecutive-day persistence rule, as a robustness check on the headline method.

## Snow side: Sierra Nevada rapid snowmelt/sublimation detection

- **`CA_snowmelt_events_detrend_5day.ipynb`** -- the headline companion notebook.
  Combined SNOTEL + MSNT + CDEC daily SWE network (312 stations, 147 daily-reporting)
  over the Sierra box. Per-station decline metric: `min(SWE over a 3-day window) -
  SWE at window start` (min-in-window, `WINDOW=3` -- adopted after stress-testing;
  see `proj_note.ipynb`), standardized per calendar day, network event = >=30% of
  reporting stations simultaneously >=1 SD below normal for >=5 gap-tolerant days.
  Includes face validity, elevation-representativeness, heat-wave match-rate,
  dry/wet rain-on-snow classification (with a station-precipitation cross-check on
  the ERA5-based call), recovery analysis, and a 2026 out-of-sample score.
- **`CA_snowmelt_methodC_5daymean_std.ipynb`** -- snow-side analog of the atmospheric
  Method C notebook, same 5-day-mean-std event definition applied to the network
  decline fraction, as a robustness check.
- **`CA_methodA_vs_methodC_match_permutation_test.ipynb`** -- standalone permutation/
  null test asking whether Method C's much higher heat-wave match rate (93% vs. Method
  A's 61%) is mostly base-rate inflation from its larger event list, or genuine excess
  detection. Self-contained: reads only the event CSVs the two notebooks above already
  export.

## Supporting notebooks

- **`plot_ca_box_map.ipynb`** -- map of the California ERA5 analysis box.
- **`snotel_box_stations_distribution.ipynb`** -- spatial/temporal coverage of the
  combined SNOTEL + MSNT + CDEC network, matching exactly what
  `CA_snowmelt_events_detrend_5day.ipynb` analyzes (312 stations, 147 daily-reporting).

## Shared library

**`ca_blocking_lib.py`** -- climatology/standardization, detrending (OLS + Theil-Sen),
gap-tolerant event detection, event-overlap pairing, and bootstrap CI helpers used by
every notebook above, so a fix only has to be made once. Has its own lightweight
self-test suite: `python ca_blocking_lib.py`.

## Data pipeline

Fetch scripts write to `DATA_DIR` (`/glade/campaign/mmm/c3we/mingge/ERA5/CA_blocking`,
not in this repo -- see `.gitignore`). Each script has a detailed header comment;
summary:

| Script | Source | Output |
|---|---|---|
| `get_z500_t700_ca.py` | ERA5 pressure levels | `z500_t700_ca_<year>.nc` (Z500, T700) |
| `get_precip_sf_ca.py` | ERA5 surface forecast | `precip_sf_ca_<year>.nc` (TP, SF) |
| `get_snotel_box.py` | NRCS AWDB (SNOTEL) | SWE, Tahoe/Carson/Walker corridor north |
| `get_msnt_box.py` | NRCS AWDB (MSNT) | SWE, southern Sierra (Yosemite-Kern) |
| `get_cdec_box.py` + `qc_cdec_swe.py` | CDEC raw telemetry | SWE, same southern terrain, heuristically QC'd |
| `check_msnt_cdec_overlap.py` | -- | crosswalk: MSNT station -> matching CDEC station |
| `build_combined_sierra_swe.py` | SNTL+MSNT+CDEC | `combined_sierra_stations.csv`, `combined_sierra_swe_wy1990-2026.csv` -- the snow notebooks' actual input |
| `get_station_precip_box.py` | NRCS AWDB + CDEC | station-measured precipitation, for the dry/wet cross-check |

`job_array_get_z500_t700_ca.pbs` / `job_array_get_precip_sf_ca.pbs` run the two ERA5
fetch scripts as PBS job arrays (one task per water year) on Casper.

## Running the notebooks

Execute with the `my_npl2026a` kernel, e.g.:

```bash
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=my_npl2026a \
  --ExecutePreprocessor.timeout=1800 \
  <notebook>.ipynb
```

Fetch scripts run in the `claude_test` conda environment (see the `.pbs` files).
