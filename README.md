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
  **Disagreement case-study linkage (2026-11-02):** the 6 ERA5/station precip
  disagreements from Section 5c were checked against this notebook's own named case
  studies (the 1997 flood, Apr 2012) -- neither overlaps; the disagreements are 6
  different, previously undiscussed events. Per-station (not just network-mean)
  breakdown shows the two "ERA5-wet" disagreements (1991-02-21/27, 2016-04-03/08) are
  spatially coherent across the network (42/44 and 27/35 stations agree it was dry,
  station medians 5%/0%) -- genuine ERA5 overestimates, the strongest relabeling
  candidates in the record. The four "ERA5-dry" disagreements split: two
  (1992-04-26/05-01, 1994-04-14/22) look like spatial mismatch (a wet minority of
  stations skews the network mean while the station median stays dry); 1996-04-26/
  05-03 (the most extreme case, 0.2% vs. 240%) is a genuinely patchy storm (16/44
  stations wet, 20/44 near zero) that ERA5's grid simply didn't resolve; 2000-05-22/30
  is the cleanest reverse-relabeling candidate (15/27 stations and the station median
  itself both wet). Net effect on the 45/13 dry/wet split is at most 46/12 of 58 --
  too small to disturb the already-null T700/Z500 match-rate result (Fisher p=1.00),
  so not rerun quantitatively.
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
  self-corrected twice.** After reading `March_2026_Western-US-Heat Wave.pdf` (Davis
  2026, see `## Related literature`) and a fresh-eyes review, two of those readings
  turned out to be domain-mean artifacts rather than real findings -- a Section 7
  follow-up (now correctly positioned after the original conclusion it follows up on,
  fixing an ordering bug a fresh-eyes review caught) splits the jet by latitude band,
  checks a NW Pacific box for Davis's reported upstream omega block, and recomposites
  IVT over just the 5-day onset window instead of the full episode mean. A second
  fresh-eyes review then caught that the NW Pacific box (140-180E) was clipped at the
  dateline, cutting off the ridge crest half of the omega pattern visible in the Feb
  and March onset panels -- widened to 150-220E and rerun. Result: no clean single
  discriminator for March's exceptional persistence, and the corrected box makes the
  non-discrimination *worse*, not better -- Davis's reported ingredients (an AR-like
  moisture plume feeding a closed NW Pacific cutoff/ridge) now show up at the onset of
  three of the four episodes, cleanest for the non-record, 7-day Late Feb episode
  immediately before March, not for March itself. Consistent with, not a resolution
  of, Davis's own admission that "the link between simultaneous blocking events is
  unclear."
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
- **`CA_ridging_persistence_drivers.ipynb`** -- *motivation:* both notebooks above test
  upstream-Pacific precursor hypotheses against a single contrast -- the four WY2026
  episodes, all from one year, because upstream Pacific fields have only ever been
  fetched for 2026. A fresh-eyes review flagged this as an n=1 case-study problem that
  more upstream diagnostics against the same contrast can't fix. This notebook pools
  the full 1990-2025 Method A event record (48 Z500 / 47 T700 events) instead, and
  tests three cheap, zero-new-fetch angles: does event intensity predict duration, does
  onset month predict duration, does local CA-box spatial structure differ between
  long- and short-duration halves. **Status: finished, null on all three.** Peak
  intensity doesn't robustly predict duration (T700's nominal Pearson r=0.33, p=0.022
  doesn't survive the more outlier-robust Spearman test, rho=0.24, p=0.10); mean
  intensity shows no relationship at all; onset month doesn't predict duration either
  (Z500 p=0.36, T700 marginal p=0.075); and long- vs. short-duration composites are
  essentially identical in amplitude (within ~1-5%, no formal difference test run).
  This is a genuinely useful negative result, not a dead end: with real statistical
  power for the first time (47-48 events, not 4), it rules out the three simplest
  possible explanations and strengthens the case that the answer, if there is one, is
  upstream rather than local -- consistent with, not a resolution of, the two notebooks
  above. Section 5's conclusion gives a concrete cost estimate (~11 GB + ~63 GB of new
  ERA5 storage, likely hours of compute) for extending the upstream-Pacific fetch to
  the full record, which this notebook deliberately does not do on its own.
- **`CA_2026_wave_activity_flux.ipynb`** -- *motivation:* re-reading
  `March_2026_Western-US-Heat Wave.pdf` closely for this thread found that Davis's own
  analysis (theta-on-DT maps, DT Hovmoller diagrams, IVT, PV-budget cross-sections)
  never computes a wave-activity flux, even though the paper's own stated "local
  cause" is a blocking anticyclone "reinforced by impinging eddies" -- exactly the
  claim a Takaya-and-Nakamura (2001) wave-activity-flux diagnostic is built to test
  directly. Computes the horizontal WAF at 300 hPa from the already-fetched
  `upstream_pacific_2026.nc` (no new fetch) for all four WY2026 episodes. **Status:
  finished, null -- and the opposite of what the hypothesis predicts.** The record
  March episode's CA-box-mean convergence (+1.4e-5 m/s^2, 53% of days convergent) is
  weaker and less sustained than the non-record, 8-day Late Jan/Feb episode (+4.1e-5,
  62% of days convergent) -- nearly 3x stronger convergence in an episode less than
  half as long. Over the wider NW-Pacific-to-CA wave path, all four episodes show net
  *divergence* on average, with no March-specific signature either way. A fourth
  consistent null result (joining intensity, onset timing, and local spatial
  structure), and a direct failure of one of Davis's two proposed mechanisms --
  consistent with Davis's own admission that "the link between simultaneous blocking
  events is unclear." Real caveats stated in the notebook: still n=1 (one season, not
  the full-record test that actually worked for local predictors), the basic state is
  2026's own seasonal mean rather than a multi-year climatology (no other year's
  upstream data exists), and the raw WAF vector field has a handful of extreme
  outlier pixels near the weak-wind mask boundary (a known numerical sensitivity of
  the Takaya-Nakamura formula, not a sign the area-averaged convergence numbers the
  conclusion rests on are wrong).
- **`CA_ridging_persistence_drivers_upstream.ipynb`** -- *motivation:* every upstream
  diagnostic above was an n=4 case study (one season); `CA_ridging_persistence_drivers.ipynb`
  found real statistical power only comes from the full 47-48-event record, but tested
  local-only predictors. The 1990-2025 upstream-Pacific fetch (`job_array_get_upstream_pacific.pbs`)
  closes that gap: this notebook re-tests Davis's two most concrete hypotheses --
  precursor NW-Pacific ridging (5-day pre-onset) and onset-window moisture transport --
  plus three secondary checks (onset-window subtropical jet, contemporaneous domain
  jet speed, contemporaneous CA-box Z300), against the full event record instead of 4
  cases. Five predictors x two variables = 10 pre-registered tests. **Status: finished
  -- the first real (non-null) signal in this investigation, with an important caveat.**
  Four of the five predictors turn out to be highly intercorrelated (Spearman |rho| up
  to 0.83) -- not independent confirmations, but one underlying "jet/trough state"
  measured four ways. For T700 it's robust even under a rough Bonferroni correction:
  precursor NW-Pac Z300 rho=-0.50 (p=0.0005), event-mean domain jet speed rho=0.43
  (p=0.0024) -- a *stronger* jet / *troughier* (not ridgier) NW-Pacific precursor
  predicts *longer* persistence. Z500 shows the same direction but weaker (p=0.07-0.15).
  Local CA-box Z300 (the one independent predictor) stays null, consistent with every
  intensity-vs-duration test elsewhere in this project. Two things keep this honest
  rather than a clean win: the sign is opposite both Davis's precursor-ridging framing
  and the informal "weak jet lets blocking persist" read of the n=4 case study; and it
  does not explain March 2026 itself -- March's own jet speed (26.8 m/s) sits at the
  31st percentile of the 48-event distribution (below average), yet March set the
  all-time duration record by a wide margin over the previous record (12 days, which
  did have an above-median jet, consistent with the general relationship). Real at the
  population level, but March is an outlier with respect to it, not a confirming case.
- **`CA_ridging_persistence_drivers_waf.ipynb`** -- *motivation:* `CA_2026_wave_activity_flux.ipynb`'s
  wave-activity-flux (WAF) diagnostic was the other upstream notebook still stuck at
  n=4 after the full-record Pacific fetch fixed it for scalar predictors; this notebook
  extends it the same way, computing the same Takaya-Nakamura formula independently per
  year (1990-2026, proxy per-year basic state kept for continuity, not switched to a
  pooled climatology) and testing three convergence-based predictors (CA-box mean,
  wider NW-Pac-to-CA path mean, fraction of event-days convergent) against the full
  47-48-event record. Weak-wind mask tightened (2 to 3 m/s) plus a new outlier backstop
  per the n=4 notebook's own flagged caveat -- confirmed to exclude only ~4.5 extra grid
  points/day, a handful-scale correction. **Status: finished, sixth (and, extended
  below, seventh) null/non-explanatory result.** Z500 duration shows no relationship to
  any of the three WAF predictors
  (p=0.46-0.75). T700 shows a weak, nominally significant but Bonferroni-uncorrected
  relationship (path-mean convergence rho=-0.31 p=0.032, fraction convergent rho=-0.32
  p=0.027) -- and it's reversed from Davis's "reinforced by impinging eddies" framing:
  more convergence predicts *shorter* persistence. March 2026 itself sits at the
  81st-94th percentile on all three measures (above-average, not a weak outlier) but
  since Z500 duration doesn't relate to these measures at all, that doesn't explain its
  record duration either -- the non-record 8-day Late Jan/Feb episode outranks March on
  two of three measures, consistent with (not contradicting) a genuine null
  relationship. Flags a possible, untested connection to the jet/trough finding above
  (a troughier precursor could be a wave-energy source rather than a local convergence
  zone) as a loose end for future work, not a resolved synthesis.
  **Extended (2026-11-02): repeated reinforcement vs. a single decaying trigger.**
  Section 4/5 only tested time-*averaged* convergence; a new Section 7 asks whether a
  long episode is long because it gets re-forced partway through (several discrete
  pulses) rather than triggered once and decaying, using the same daily series already
  computed (no new data). Predictors are rate/fraction-based specifically to avoid the
  tautology that a longer event mechanically fits more raw pulse counts. Also null for
  Z500 (p=0.23, p=0.94) and only marginal-and-reversed for T700 (pulse rate rho=-0.29
  p=0.052, second-half-convergent fraction rho=-0.29 p=0.051 -- *more* frequent/
  sustained pulses go with *shorter* T700 persistence, not longer) -- weaker than the
  time-mean result, same direction, not an independent confirmation. March's 19-day
  sequence shows 5 distinct pulses (more than any WY2026 sibling in raw count) but its
  rate-normalized pulse rate (69th percentile) and second-half-convergent fraction
  (63rd percentile, *lower* than the short Late Jan/Feb episode's 85th) are both
  unremarkable -- the "recharging" hypothesis is now also closed out as a seventh
  null/non-explanatory result, cheap to test and worth ruling out rather than leaving
  open.
- **`CA_ridging_persistence_background_state.ipynb`** -- *motivation:* every notebook
  above tests an instantaneous precursor or contemporaneous field; none test
  *background* conditions -- the slower large-scale state an episode happens to occur
  within. Davis flags "an inactive MJO" for March 2026 as a single-case observation;
  ENSO and PDO were never tested at all. First use of non-ERA5, non-station data in
  this project (`get_mjo_enso_pdo_indices.py` fetches public NOAA ONI/PDO/OMI indices).
  **Status: finished -- the strongest statistical result in the mechanism thread, and
  the first one that can't be checked against March at all.** PDO event-mean rho=0.46
  (p=0.0009, n=48) clears a 6-test Bonferroni bar (p<0.0083) with room to spare -- a
  warm PDO phase predicts longer Z500 ridging persistence specifically (T700: rho=0.17,
  not significant) -- physically plausible given the literature's association of
  warm-PDO/El-Nino-like regimes with persistent West Coast ridging (e.g. 2013-2015's
  "Ridiculously Resilient Ridge"). But NOAA's PDO series currently ends August 2025 --
  there is no 2026 value, so this one Bonferroni-robust predictor cannot be evaluated
  for March 2026 itself; not a null result, a data-availability gap. ENSO (ONI) is
  nominally significant for Z500 (rho=0.34, p=0.018) but does not survive correction,
  and March's own ONI (0.11, ENSO-neutral) sits at exactly the 50th percentile -- dead
  center, not an outlier. MJO shows no relationship to duration at all (continuous or
  active/inactive split, p=0.32-0.67), and March's own mean OMI amplitude (1.02,
  range 0.91-1.07, 63% of days "active") is a weak but not clearly inactive signal --
  a direct, mild correction to the qualitative claim that motivated this check.
- **`CA_ridging_persistence_season_clustering.ipynb`** -- *motivation:* every notebook
  above treats the *episode* as the unit of analysis -- what made March's 19 days long.
  A different framing: WY2026 had four Z500 episodes packed into a 79-day span with
  gaps of only 11, 18, and 10 days -- maybe the anomaly is the *season* regenerating
  ridges faster than normal (no recovery window), not one episode's internal dynamics.
  Tests episode count, total days-in-episode, and inter-episode gaps at the season
  level (one row per water year) against the 1990-2025 record, and whether season-mean
  ENSO/PDO predict clustering specifically (not just single-episode duration). No new
  fetch. **Status: finished -- the clearest, least caveated finding in the mechanism
  thread, but still doesn't explain 2026 itself.** 2026 is the literal record-holder
  (100th percentile of 36 fit-period seasons) on every season-coverage metric for both
  Z500 and T700: 4 episodes, 43-46 total episode-days, 36-38% of the whole Jan-Apr
  season spent in an active episode -- more than any prior year on every measure
  simultaneously, not an outlier on just one axis. Its inter-episode gaps sit in the
  tight tail (Z500: 12th percentile of 16 multi-episode seasons; T700: 6th-11th
  percentile of 18), confirming "no chance to recover" quantitatively. Season-mean
  ENSO/PDO show a real, coherent (same direction as the single-episode PDO result)
  relationship to gap tightness specifically -- T700 min-gap vs. ENSO rho=-0.61
  (p=0.0078, n=18), vs. PDO rho=-0.48 (p=0.042, n=18); Z500 weaker (p=0.06-0.09) --
  though none clear a 12-test Bonferroni bar and the multi-episode-season sample is
  small. Episode count/total days show no ENSO/PDO relationship at all (p=0.15-0.93) --
  background state, if it matters, acts on spacing, not overall frequency. But 2026's
  own season-mean ONI (-0.01) is almost exactly neutral, not the El-Nino-like state
  that would predict tight clustering, and PDO can't be checked (no 2026 data) -- so
  even this relationship fails to explain 2026's own record-breaking clustering. Across
  eight notebooks and roughly a dozen hypotheses, this sharpens *what* needs explaining
  (season-long regeneration, not single-episode decay) without yet explaining it.
- **`CA_ridging_persistence_antecedent_snowpack.ipynb`** -- *motivation:* a
  genuinely project-native hypothesis connecting the clustering finding to a land-
  atmosphere feedback running the opposite direction from everything else tested:
  does a ridging episode's own snowmelt leave the surface anomalously dry/depleted,
  priming the *next* episode (less evaporative cooling, more sensible heating) to
  persist longer -- and did WY2026's three pre-March episodes progressively prime
  March itself? Builds a network-mean standardized Sierra SWE-*level* anomaly (per-
  station calendar-day climatology, fit 1990-2025, averaged across stations --
  deliberately not a raw mm average, which this project's snow-side notebooks have
  repeatedly flagged as station-composition-biased) from the combined SNOTEL+MSNT+CDEC
  network already built for the snow-side notebooks -- no new fetch. **Status:
  finished -- contradicted, not just null, and the sharpest single discrepancy for
  March found so far.** The population relationship runs *opposite* to the hypothesis:
  antecedent SWE-level anomaly vs. Z500 duration is rho=0.34 (p=0.017, n=48) --
  *positive* -- events preceded by above-normal, not depleted, snowpack tend to last
  slightly longer (T700: same direction, rho=0.15, not significant). March's own
  antecedent anomaly was the most depleted of its own season (-0.87 to -0.90 sigma,
  17th-19th percentile of the full record) -- under the relationship just found, that
  should predict a *shorter* episode, not the longest on record by a wide margin. The
  within-season trajectory does trend toward depletion (Jan +0.10 -> March -0.87) but
  isn't a clean monotonic cascade (a flat step between the second and third episodes).
  Notes, without testing, that the reversed relationship could be a byproduct of the
  same PDO/ENSO background state already implicated elsewhere rather than a causal
  effect of snow abundance itself. Sets aside this specific (depletion-priming) form
  of land-atmosphere feedback as an explanation for March.
- **`CA_ridging_persistence_quasi_resonance.ipynb`** -- *motivation:* tests quasi-
  resonant amplification (QRA; Petoukhov et al. 2013, Coumou et al. 2014) -- a
  specific, formal mechanism distinct from two prior null results that sound similar:
  not discrete reinforcement pulses (`CA_ridging_persistence_drivers_waf.ipynb`), not
  whole-field phase speed (`CA_2026_dynamic_tropopause_diagnosis.ipynb`), but whether a
  particular large-scale wave gets trapped by a waveguide (a double jet) and amplifies
  in place with near-zero *wave-specific* phase speed. **Two real limitations stated up
  front:** this project's upstream field is regional (~110 degrees of longitude, ~30%
  of a full latitude circle), not global, so a true wavenumber-6-to-8 decomposition
  isn't possible -- this notebook fits a single dominant large-scale harmonic across
  the available sector instead, an honestly-labeled proxy, not a genuine wavenumber
  attribution; and it uses fixed-pressure Z300 (matching the WAF/jet notebooks and the
  QRA literature's own convention) rather than the dynamic tropopause, which gets it a
  real full-record test instead of the DT notebook's unavoidable n=1. **Status:
  finished -- March scores at the wrong end of every proxy measure tested.** Population
  relationships are weak and mixed: wave amplitude nominally positive for T700 only
  (rho=0.32, p=0.028, null for Z500), |phase speed| QRA-consistent in direction for
  both variables but not significant (p=0.21, p=0.43), and the jet double-core
  (waveguide) ratio -- the actual precondition QRA depends on -- nominally significant
  for Z500 but **backwards** (rho=-0.34, p=0.020: more double-jet structure predicts
  *shorter* persistence). None of six tests clears a Bonferroni bar. March itself: 8th
  percentile wave amplitude (one of the *least* amplified large-scale waves in 36
  years), 79th percentile |phase speed| (faster, not stationary), and the single
  highest double-jet ratio in the entire record (100th percentile) -- which, given that
  metric's negative population relationship, makes March's record duration a second-
  order anomaly even on the one measure where it's extreme. Quasi-resonant
  amplification, at least in this regional-proxy form, joins the list of mechanisms
  that do not explain March; a genuine global-wavenumber test remains a real, uncosted
  option for ruling out the formal version of the theory.
- **`CA_ridging_persistence_gap_trough_depth.ipynb`** -- *motivation:* a specific
  refinement of a proposed hypothesis ("repeated ridge development plus insufficient
  intervening trough passage matters more than individual-ridge intensity") whose
  other two claims were already established -- repeated development is real and
  record-breaking (`CA_ridging_persistence_season_clustering.ipynb`), intensity is null
  (`CA_ridging_persistence_drivers.ipynb`). The third claim was never actually tested:
  the clustering notebook measured gap *length* only, not whether the circulation ever
  reached genuine trough conditions during those gaps. Builds two gap-depth metrics
  (minimum standardized anomaly reached in the gap; fraction of gap-days at or below
  -1 sigma, symmetric to the ridge-detection threshold) from the standardized Z500/T700
  series already used throughout this project -- no new fetch. **Status: finished --
  the first mechanism in this thread where March's own case supports, rather than
  contradicts, the pattern, though the statistical backing is suggestive, not
  confirmed.** Event-level: gap minimum anomaly predicts the *following* episode's
  duration for Z500 (rho=0.51, p=0.025, n=19) in the hypothesized direction (shallower
  trough -> longer episode); T700 weaker, not significant (rho=0.34, p=0.156). Doesn't
  clear a 4-test Bonferroni bar (p<0.0125). Season-level test (season's weakest trough
  vs. total season episode-days): consistent direction for Z500 (p=0.12-0.24, not
  significant) but T700's fraction-based metric is wrong-signed (rho=+0.21) -- not a
  clean cross-variable confirmation. **But WY2026's own three gaps illustrate the
  hypothesis cleanly:** two of three never reached -1 sigma at all, and the gap
  immediately preceding March (Mar 2-10) was the *shallowest of WY2026's own three
  gaps* (min_sanom=-0.16, 95th percentile shallow) -- immediately followed by the
  19-day record episode. Every prior mechanism in this thread (jet speed, WAF
  convergence/pulses, antecedent snowpack, QRA amplitude/phase/waveguide) had March as
  an outlier *against* its own relationship; this is the first where March's case
  aligns with it. Flagged explicitly as a lead worth a larger/more rigorous follow-up
  (n=19 is small, doesn't survive correction, T700 doesn't confirm), not a settled
  explanation -- but the most promising candidate this mechanism thread has produced.
- **`CA_ridging_persistence_central_pacific_template.ipynb`** -- *motivation:* did
  WY2026's four episodes share a recurring central-Pacific precursor disturbance (a
  "stuck" pattern regenerating similar ridges), or were they four independently
  different-looking triggers that happened to produce similar outcomes? Earlier
  precursor tests only ever used box-mean scalars; this is the first to compare
  precursor *spatial patterns* directly. Uses a standard central-Pacific box
  (160-220E, 20-40N, distinct from Davis's NW-Pacific omega-block box) from data
  already in hand, Z500 episodes only. **Status: finished -- a field-dependent split.**
  Z300 (dynamical disturbance shape): WY2026's four precursor maps are **not** more
  similar to each other than chance -- mean pairwise correlation -0.07, 25th percentile
  of a 2000-draw bootstrap null from the 47-event fit-period record (mean 0.094) --
  if anything slightly *less* similar than a random historical set. IVT (moisture-
  plume shape): WY2026's four precursor maps **are** more similar than typical -- mean
  pairwise correlation 0.24, 91st percentile of the same null (suggestive, one-sided
  empirical p~0.09, not strict significance at n=4). Physical reading offered
  carefully: the upper-level wave shape differed each time, but the moisture pathway
  feeding each new disturbance was unusually consistent -- closer to Davis's "Anti-AR"
  moisture-stream framing than a literal repeating wave template. Speculatively
  connects to `CA_ridging_persistence_gap_trough_depth.ipynb`'s shallow-trough finding
  as two independent signatures of the same idea (the background state staying fixed
  rather than resetting between episodes) -- not tested jointly, a real next step.
- **`CA_ridging_persistence_trough_moisture_join.ipynb`** -- *motivation:* tests the
  "real next step" flagged above directly: does the moisture pathway feeding the
  episode before a gap resemble the one feeding the episode after it
  (`ivt_pair_corr`, same precursor-map method as the template notebook, computed
  per-gap across the full record instead of once for WY2026), and does *that*
  predict a shallower trough or longer following episode, the way gap depth itself
  does? Z300 (`z300_pair_corr`) is kept as an explicit dynamical control, since the
  template notebook found no dynamical recurrence. Z500 only, no new fetch.
  **Status: finished -- the join does not hold; the two findings are statistically
  independent.** All six tests (2 pathway variables x 2 gap-depth metrics, plus 2
  direct tests against following duration) are null at n=18 fit-period gaps
  (p=0.08-0.90); nothing clears even a nominal 0.05 bar. The direct collinearity
  check is the most informative result: `ivt_pair_corr` vs. `gap_min_sanom` is
  essentially uncorrelated (rho=0.11, p=0.663) -- whether a gap's trough was shallow
  and whether the moisture pathway persisted across it vary independently at the
  population level. WY2026's own three gaps don't tell a clean story either: only
  the gap immediately before March pairs elevated pathway persistence (78th
  percentile) with its shallow trough (94th percentile), but the dynamical control
  is equally elevated for that same gap (78th percentile), undercutting a
  moisture-specific reading; the other two WY2026 gaps show no such alignment, and
  the one gap with a genuinely deep trough (the Feb gap, 33rd percentile) has
  exactly median pathway persistence, not the suppressed value a "conveyor prevents
  troughs" story would predict. This notebook's three consecutive-pair IVT
  correlations exactly reproduce three of the template notebook's six pairwise
  values, confirming the computation matches -- and shows that notebook's 91st-
  percentile season-wide result was not driven uniformly by adjacent-episode
  persistence; it also reflects non-adjacent pairs this notebook didn't test. Net:
  the gap-trough-depth and central-Pacific-template findings should continue to be
  treated as two separate, individually-suggestive leads, not components of one
  mechanism -- this specifically rules out one being explained by the other.

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
| `get_mjo_enso_pdo_indices.py` | NOAA PSL (public, no ERA5/station data) | `oni_index.csv`, `pdo_index.csv`, `omi_index.csv` -- ENSO/PDO/MJO background-state indices, for `CA_ridging_persistence_background_state.ipynb` |

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
