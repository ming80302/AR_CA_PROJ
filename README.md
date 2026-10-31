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

**A third thread, opened after March 2026 set records on both sides of that
question simultaneously:** *why* do some ridging episodes persist far longer than
others? The detection/matching work above treats every heat-wave event the same way
regardless of duration; the March 2026 episode (19 days, vs. 7-9 days for its three
WY2026 predecessors) motivated pulling upstream Pacific-basin fields and comparing
them against the companion synoptic analyses this project is built on (see
`## Mechanism` below and `## Related literature`).

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
- **`CA_snowmelt_april_vs_janmar_match_test.ipynb`** -- *motivation:* a fresh-eyes
  climate-scientist review was asked to sanity-check a proposed storyline ("apart from
  a few atmospheric rivers, Z500/T700 indicates melt events well, and perhaps better
  later in the season") against the project's own numbers -- the raw month-by-month
  match rate instead showed it peaking in March and dropping sharply in April, the
  single most common onset month (59% of the Jan-Apr sample), the opposite of the
  proposed claim. This notebook puts a formal test behind that finding. Fisher exact +
  bootstrap CI confirm a real April drop for Z500 (p=0.0014) that survives
  (direction-wise) under Method C's heat-wave record too, though Method C's
  near-ceiling Jan-Mar match rate (100%) leaves little room to detect it there. Also
  tests whether unmatched April events are smaller/more routine (they aren't -- same
  size as matched ones, all magnitude comparisons indistinguishable). Discusses Guo and
  He (2026, see `## Related literature`) as a literature-backed explanation: reduced
  spring snowpack cold content may lower the physical bar for rapid melt, independent
  of whether a synoptic heat wave is detected. **Status: finished** -- executed clean,
  fresh-eyes-reviewed against both reference papers, one minor citation imprecision
  (paper says persistence is longest in spring *and winter*, tied, not spring alone)
  fixed.
- **`CA_t2m_local_heatwave_vs_snowmelt.ipynb`** -- direct follow-up testing the Guo-and-He
  explanation above rather than just citing it: builds a local (Sierra-box T2M)
  quantile-exceedance heat-wave definition, swept across the general relative-threshold
  range Guo and He cite from the broader heatwave literature (90th/95th percentile x
  2-5 day minimum persistence), and matches it against the same melt events instead of
  the synoptic Z500/T700 record. Finds the April gap nearly disappears at the loosest
  (2-day) setting but reopens at longer required persistence -- refining the
  cold-content story into a *persistence-threshold* effect (April melt needs only a
  brief warm pulse, not a sustained one) rather than a simple local-vs-synoptic scale
  effect. **Status: finished, fresh-eyes-reviewed.** One attribution fix: the
  90th/95th-percentile, 2-5-day range is the general literature context Guo and He cite
  (Robinson 2001; Perkins and Alexander 2013) while reviewing common heatwave
  definitions, not a confirmed statement of their own specific method (deferred in the
  paper to a supporting-information file this project doesn't have) -- the notebook
  originally overstated that attribution in five places, now corrected.

## Mechanism: why do some ridging episodes persist longer than others?

Everything above treats heat-wave *detection* and event-level *matching* -- this new
thread asks what differentiates a 19-day record episode (March 2026) from an ordinary
7-9 day one, using upstream Pacific-basin fields the detection notebooks never pull
(they only ever look at the small CA box). Both notebooks here reproduce the four
WY2026 Z500 episode windows directly from the frozen 1990-2025 baseline (not
hardcoded), so they can't silently drift from `CA_z500_t700_blocking_events_detrend_5day.ipynb`
Section 8's own numbers.

- **`CA_2026_upstream_mechanism_composite.ipynb`** -- *motivation:* directly prompted
  by the question "what allowed the dry warm conditions to persist for so long?" after
  discussing how exceptional the March 2026 episode was. First look, using
  fixed-pressure composites (Z300, 300 hPa jet speed, SST, IVT) over a wide
  Pacific-North America domain, explicitly an n=1, non-anomaly (no historical upstream
  baseline yet) case-study -- motivates a test, isn't one. The first pass found a
  CA-box Z300 highest and domain-mean jet speed lowest during the record March episode,
  read at the time as a weakened-jet / no-omega-block signature. **Status: finished,
  self-corrected.** After reading `March_2026_Western-US-Heat Wave.pdf` (Davis 2026,
  see `## Related literature`) and a fresh-eyes review, two of those readings turned
  out to be domain-mean artifacts rather than real findings -- a Section 7 follow-up
  (now correctly positioned after the original conclusion it follows up on, fixing an
  ordering bug a fresh-eyes review caught) splits the jet by latitude band, checks a
  NW Pacific box for Davis's reported upstream omega
  block, and recomposites IVT over just the 5-day onset window instead of the full
  episode mean. Result: no clean single discriminator for March's exceptional
  persistence -- Davis's reported ingredients (an AR-like moisture plume feeding a NW
  Pacific block) show up at the onset of *both* March and a non-record 8-day episode
  six weeks earlier, so they look necessary-ish but not sufficient. Consistent with,
  not a resolution of, Davis's own admission that "the link between simultaneous
  blocking events is unclear."
- **`CA_2026_dynamic_tropopause_diagnosis.ipynb`** -- follow-up using the dynamic
  tropopause (2-PVU surface) instead of a fixed pressure level, after reading the
  source analysis this project is partly built on (`March_2026_Western-US-Heat
  Wave.pdf`, see below) and realizing a fixed-level composite can't resolve the
  structure that paper actually found (a strengthened subtropical jet from a second,
  upstream NW Pacific block -- not a weakened jet overall, which a naive domain-mean
  misleadingly suggested). Reproduces the paper's theta-on-DT map and DT Hovmoller
  diagnostics. **Status as of this README update: built and validated (the PV/theta
  interpolation routine is unit-tested against synthetic columns), but the underlying
  `upstream_pv_theta_2026.nc` extraction (`get_upstream_pv_theta.py`) was still running
  at time of writing -- not yet executed against real data.**

## Supporting notebooks

- **`plot_ca_box_map.ipynb`** -- map of the California ERA5 analysis box.
- **`snotel_box_stations_distribution.ipynb`** -- spatial/temporal coverage of the
  combined SNOTEL + MSNT + CDEC network, matching exactly what
  `CA_snowmelt_events_detrend_5day.ipynb` analyzes (312 stations, 147 daily-reporting).

## Related literature

Not part of the repo (kept in `~/ERA5/`, referenced for context):

- **`March_2026_Western-US-Heat Wave.pdf`** (Chris Davis, UMass Amherst/NCAR/Paros
  Center, June 2026) -- "The Anti-AR of March 2026," a dynamic-tropopause/PV analysis
  of the same record event this project's 2026 out-of-sample test independently
  flagged. Source of the upstream-mechanism framing in `CA_2026_dynamic_tropopause_diagnosis.ipynb`
  above: a quasi-persistent Western US block reinforced by impinging eddies, an
  upstream NW Pacific omega block that built an anomalously strong subtropical jet,
  an inactive MJO, and an AR-like moisture stream feeding diabatic heating into the
  ridge from upstream (title's "Anti-AR" paradox: an AR helped build the dry ridge).
- **Guo and He (2026)**, *Environ. Res. Lett.* 21 194013, "Heatwaves drive rapid
  snowmelt and disrupt streamflow in the western United States"
  (`Guo_2026_Environ._Res._Lett._21_194013.pdf`) -- a published, WUS-wide (823 SNOTEL
  stations, 2001-2024) companion study using a local station-temperature-percentile
  heatwave definition rather than this project's synoptic Z500/T700 index. Key
  parallel finding: even though ~98% of local heatwave periods show accelerated
  snowmelt, only 55% of heatwave-impacted watersheds show a detectable streamflow
  response -- the same "near-universal at the proximate step, only moderate one step
  downstream" pattern this project keeps finding. Their spring cold-content mechanism
  is cited in `CA_snowmelt_april_vs_janmar_match_test.ipynb`'s conclusion as a
  candidate explanation for the April match-rate drop.

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
| `get_upstream_pacific.py` | ERA5 pressure levels + surface + vertically-integrated | `upstream_pacific_<year>.nc` (Z300, U300, V300, MSLP, SST, cloud cover, IVT components) over a wide Pacific-North America domain, for the mechanism composite notebook |
| `get_upstream_pv_theta.py` | ERA5 pressure levels | `upstream_pv_theta_<year>.nc` (PV, T, U, V on an 11-level 500-50 hPa bracket), for locating the dynamic tropopause |
| `get_t2m_sierra.py` | ERA5 surface | `t2m_sierra_<year>.nc` (Sierra-box 2m temperature, 1990-2026), for the Guo-and-He-style local-heatwave comparison (`CA_t2m_local_heatwave_vs_snowmelt.ipynb`) |

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
