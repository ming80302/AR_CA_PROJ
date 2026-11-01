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
  Combined SNOTEL + MSNT + CDEC daily SWE network (404 stations, 150 daily-reporting
  -- revised 2026-11-01, see station-count note below) over the Sierra box.
  Per-station decline metric: `min(SWE over a 3-day window) -
  SWE at window start` (min-in-window, `WINDOW=3` -- adopted after stress-testing;
  see `proj_note.ipynb`), standardized per calendar day, network event = >=30% of
  reporting stations simultaneously >=1 SD below normal for >=5 gap-tolerant days.
  Includes face validity, elevation-representativeness, heat-wave match-rate,
  dry/wet rain-on-snow classification (with a station-precipitation cross-check on
  the ERA5-based call), recovery analysis, and a 2026 out-of-sample score.
  **Data-quality note (2026-10-31):** the station precipitation cross-check's CDEC
  feed has a real, only partially correctable issue -- see `get_station_precip_box.py`
  -- where some stations' raw telemetry "pegs" at suspiciously round values (e.g.
  exactly 5.0 in recurs 76 times across unrelated stations/dates); a plausibility
  filter now removes the most extreme corruption (values up to several meters/day),
  but subtler round-value artifacts remain undistinguishable from genuine extremes.
  Section 5c's cross-check numbers were revised accordingly (Spearman rho 0.44, not
  the earlier ~0.5; 3 of 45 "dry" events now show a reverse disagreement against
  station gauges, not zero) -- see the notebook's own Section 5c conclusion for the
  full caveat.
  **Station-count note (2026-11-01):** `get_snotel_box.py`/`get_msnt_box.py` were
  fetching AWDB with `activeOnly=true`, and `get_cdec_box.py` with CDEC's equivalent
  active-station filter -- both silently drop stations decommissioned before today
  even if they have real data inside this project's 1990-2026 study window (verified
  live: 5 of 72 in-box MSNT stations and 92 of 367 in-box CDEC stations were being
  dropped this way). Fixed to filter by date-range overlap with the study period
  instead of current active status; the combined network grew from 312 to **404
  stations** (150 daily-reporting, up from 147: 36 SNTL + 72 MSNT, up from 67 + 296
  CDEC, up from 209). All headline numbers in this README and the snowmelt notebooks
  below have been recomputed against the corrected, larger network.
- **`CA_snowmelt_methodC_5daymean_std.ipynb`** -- snow-side analog of the atmospheric
  Method C notebook, same 5-day-mean-std event definition applied to the network
  decline fraction, as a robustness check. **Numbers revised (2026-10-31):** its
  climatology/trend fit wasn't actually restricted to the 1990-2025 fit years the way
  the per-station layer above it was, letting WY2026 leak into the "frozen" baseline
  despite the notebook's own `YEARS` comment saying it was excluded (`ca_blocking_lib.py`
  bugfix, see commit history). Correcting that moved the headline Method C counts from
  122/56/26 to **127/64/31** (1/2/3 sigma) and the "5-day-mean narrower than daily"
  bootstrap result from 17.6% to **19.2%** (90% CI [17.9%, 20.7%]); the real-Method-A
  match rate against Method C also shifted from 55/58 (95%) to 57/58 (98%). All
  qualitative conclusions are unchanged -- Method C is still a ~5x looser event-counting
  method than its matched control and still not defensible as a sigma-based ranking
  method -- only the specific numbers moved.
  **Numbers revised again (2026-11-01):** the station-count fix above (312->404
  stations) moved the Method C counts from 127/64/31 to **129/62/29** (1/2/3 sigma)
  and the bootstrap-narrower result from 19.2% to **19.3%** (90% CI [18.0%, 20.7%]);
  the real-Method-A match rate against Method C stayed at 57/58 (98%). Again, no
  qualitative conclusion changed.
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
  Wave.pdf`, see below) and realizing a fixed-level composite can't resolve ridge
  structure the way a dynamically-correct surface can. Reproduces the paper's
  theta-on-DT map and DT Hovmoller diagnostics. **Status: finished, including a
  retraction.** The theta-on-DT maps hold up well -- March shows the broadest,
  smoothest amplified ridge of the four episodes. The Hovmoller's initial read (a
  normal propagating wave that "visibly stalls" into blocking during March) did
  **not** survive quantification: a whole-field phase-speed scan (Section 5, after two
  cruder methods -- day-to-day peak tracking and two-point lag correlation -- failed
  or gave inconsistent results) finds the *same* ~4-6 m/s eastward phase speed before
  and during the March episode, with March's fit if anything cleaner, not slower. The
  "textbook blocking" claim is retracted, not softened -- most likely an amplitude
  illusion (March's anomaly was much larger, not slower-moving). Net result: across
  both upstream notebooks, nothing tested so far (jet speed, NW Pacific ridging,
  onset-window moisture, or now wave phase speed) explains why March persisted three
  times longer than its WY2026 predecessors -- `CA_2026_upstream_mechanism_composite.ipynb`
  Section 7's open question is still open.

## Method A vs. Method C: cross-cutting comparison

Both the atmospheric and snow sides define a headline "Method A" (explicit threshold +
consecutive-day persistence rule) and a "Method C" (smooth first -- a 5-day rolling
mean, or the snow side's already-derived decline metric -- then threshold *that*
series against its own distribution with `min_duration=1`, folding persistence into
the smoothing instead of asserting it separately). Method C's inclusion rule is
structurally looser by construction (a single day where the smoothed series crosses
threshold counts, vs. Method A's requirement that 5 *raw* days each individually
clear it), so "Method C finds more events everywhere" is expected, not itself a
finding -- the real question is whether the extra events are physically meaningful or
just noise, and whether sigma-based ranking still means the same thing once you've
smoothed.

**Atmospheric (Z500/T700): Method C behaves well.** Every Method A event (48/48 Z500,
47/47 T700) has an overlapping Method C episode -- a strict superset, not a different
phenomenon. Method C finds ~2.9x more events (139/137 vs. 48/47) and ~2x more
event-days (17% vs. 8% of the Jan-Apr record). The 5-day-mean distribution is 19-20%
narrower than daily (bootstrap CI excludes zero), consistent with ordinary synoptic
autocorrelation -- nothing pathological. Because Z500/T700 are continuous,
free-running fields with comparable variance all season, **ranking by peak sigma
remains physically meaningful** (subject only to the ordinary winner's-curse caveat of
picking a top-10 from noisy data).

**Snow (Sierra SWE rapid decline): Method C is much messier.** Against a matched
control built on the same raw substrate (Method A', 1-day SWE diff with Method A's
persistence rule), Method C finds ~5x more events (129 vs. 25) -- a bigger inflation
than the atmospheric side's 2.9x -- and only 18% of its episodes have any Method A'
counterpart at all. Containment of the real headline Method A is nearly but not
perfectly complete (57/58, one exception). Critically, **ranking by peak sigma is not
just noisier here, it's actively misleading**: the Sierra network-decline fraction is
a bounded, zero-inflated quantity whose climatological variance is ~8x smaller in
January than April, so a sigma-based "largest events" list ranks modest January blips
above genuinely larger April melt episodes -- the opposite of the atmospheric side's
behavior, and a direct, generalizable consequence of seasonal heteroscedasticity that
a naive port of the Z500/T700 approach would have silently inherited. Use raw
`peak_frac` or an empirical percentile to rank snow-side events, never `peak_sanom`.

**Cross-domain: does Method C's looser heat-wave definition predict snowmelt
better?** Genuinely mixed, not a clean win for Method C. Raw match rate against Sierra
rapid-decline events jumps from 61%/59% (Method A) to 93%/93% (Method C), and a
permutation test confirms this isn't pure base-rate inflation from a denser event
calendar (Method C's excess over its own, higher chance baseline is larger, not
smaller, than Method A's: +62 vs. +47 points). But the properly-controlled
block-level test only marginally favors Method C (p=9.8e-13 vs. 4.1e-12 -- both
overwhelming, practically indistinguishable), and the raw day-level enrichment ratio
actually favors Method A (3.1x vs. 2.7x), since Method C's larger, more inclusive
calendar dilutes that particular contrast. Four different statistics (match rate,
permutation excess, block p-value, enrichment ratio) rank the two methods three
different ways depending on which one is asked -- that is an honest
recall-vs-precision tradeoff to report in full, not an artifact to resolve into one
number.

**Conclusion and recommendation.** Method A remains the primary, headline definition
on both sides: simpler, more interpretable, and -- critically on the snow side --
free of a ranking method that is actively wrong. Method C is a validated robustness
check, not a replacement, and its reliability is asymmetric: trustworthy for both
counting and ranking on the atmospheric side, trustworthy only for counting (never
ranking) on the snow side. The generalizable lesson is about homoscedasticity, not
Method A vs. C specifically -- a standardize-then-smooth-then-rank approach is safe on
a continuous, roughly-constant-variance physical field and dangerous on a bounded,
seasonally heteroscedastic derived quantity; checking whether a new variable's
variance is stable across the season, before porting this kind of method to it, would
catch this class of problem before it requires a dedicated stress-test section to
discover. For the applied question "does a looser atmospheric heat-wave definition
better explain snowmelt," the honest answer is mixed: a win on recall that survives a
permutation-test sanity check, but a wash or a loss on the two statistics that control
for Method C's larger event calendar -- anchor downstream claims on Method A's
cleaner, matched comparison and treat Method C's numbers as corroborating, not
decisive, exactly as `CA_methodA_vs_methodC_match_permutation_test.ipynb` already
frames it.

## Supporting notebooks

- **`plot_ca_box_map.ipynb`** -- map of the California ERA5 analysis box.
- **`snotel_box_stations_distribution.ipynb`** -- spatial/temporal coverage of the
  combined SNOTEL + MSNT + CDEC network, matching exactly what
  `CA_snowmelt_events_detrend_5day.ipynb` analyzes (404 stations, 150 daily-reporting).

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
