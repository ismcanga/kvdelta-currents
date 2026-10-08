# KVDelta Currents

An open research project for testing **KVΔ (K-V-Delta)** against public ocean-current data.

The project starts with archived observations and reanalysis products, where predictions can be tested honestly against already-known future states. If the method survives that stage, the same pipeline can later be applied to near-real-time ocean-current feeds.

## KVΔ working model

KVΔ is treated here as a falsifiable structural hypothesis, not as a forecasting claim.

- **K** — known or bounding information: measured conditions, constraints, geometry, environmental context, or other inputs defining what movement is possible.
- **Δ** — an additional co-determining dimension: the component needed with K to account for the resulting state or transition. It is not merely an after-the-fact error term.
- **V** — the resulting state, direction, magnitude, coordinate, or other observable outcome produced by the relationship between K and Δ.

A useful analogy is a 3-4-5 triangle: K=3, Δ=4, V=5. V is not K+Δ; K and Δ jointly determine V through a relationship that must be discovered or tested.

The project does **not** assume in advance that KVΔ works. The objective is to define measurable tests under which it can fail.

## First research question

> Given an ocean-current state at time t and a bounded set of observable conditions K, can a KVΔ representation predict or explain the current state at t+n better than simple baselines?

Initial targets:

1. Current direction change.
2. Current speed change.
3. Advection / displacement of a virtual drifter.
4. Regime transitions: strengthening, weakening, turning, persistence.

## Data

Primary candidate: **Copernicus Marine Service**.

Useful products include:

- Global surface currents at 0.25° resolution, hourly/daily/monthly, with multi-year data beginning in 1993.
- Near-real-time global surface-current fields.
- In-situ current observations from drifting buoys, Argo floats, and HF radar.
- Global ocean physics reanalysis at ~0.083° daily resolution for broader physical context.

See `docs/DATA_SOURCES.md`.

## Phase 0 — falsification before forecasting

Start with a geographically bounded region and a fixed historical interval.

Suggested first region: **North Pacific**, because it contains persistent large-scale circulation while still exhibiting seasonal and mesoscale variation.

Workflow:

1. Download a fixed historical slice.
2. Split chronologically into discovery / validation / sealed test periods.
3. Define K, Δ and V without looking at the sealed test outcomes.
4. Compare KVΔ against trivial baselines:
   - persistence: V(t+n) = V(t)
   - climatology
   - local linear trend
   - simple autoregression / nearest-neighbour baseline
5. Score direction, speed and displacement errors.
6. Publish failures as well as successes.

## Phase 1 — retrospective experiments

The first useful experiment should be intentionally small:

- Region: North Pacific box
- Grid: 0.25° surface product
- Cadence: hourly or daily
- Horizon: 6 h, 24 h, 72 h
- Variables: eastward velocity (u), northward velocity (v), position/time, optionally wind stress and sea-surface temperature
- Output: one deterministic CSV/Parquet result table plus plots

The experiment is successful only if KVΔ beats declared baselines on the sealed test period and the advantage reproduces on another time interval or region.

## Phase 2 — independent observations

Use in-situ drifter and Argo measurements as an external check rather than relying only on gridded model/reanalysis products.

## Phase 3 — near-real-time

Only after retrospective validation:

1. Freeze the method and parameters.
2. Fetch a near-real-time current field.
3. Emit timestamped predictions before the target observation exists.
4. Store prediction hashes / immutable records.
5. Score them later against newly arrived observations.

This turns the project from retrospective fitting into a public prospective test.

## Repository principles

- Open data only.
- Free/open-source implementation.
- Deterministic experiments where possible.
- No hidden training data.
- Clear separation between observation, transformation, hypothesis and score.
- Baselines are mandatory.
- Negative results stay in the repository.
- Avoid grand claims: this is an experiment until independently reproduced.

## Proposed layout

```text
kvdelta-currents/
├── README.md
├── LICENSE
├── CITATION.cff
├── docs/
│   ├── DATA_SOURCES.md
│   ├── EXPERIMENT_001.md
│   └── KVDELTA_CONTRACT.md
├── data/
│   └── README.md
├── experiments/
├── src/
└── results/
```

Large source datasets should not be committed to Git. Store download recipes, checksums and provenance instead.

## Status

**Stage 0: project definition.** No predictive claim has been established.

## License

MIT. Data retain the licenses and attribution requirements of their original providers.

## GitHub automation and hosted site

The repository includes two GitHub Actions workflows:

- `.github/workflows/ci.yml` validates the project structure and generated status on pushes and pull requests.
- `.github/workflows/pages.yml` publishes `site/` to GitHub Pages whenever `main` changes.

After creating the repository, open **Settings → Pages → Build and deployment** and select **GitHub Actions** as the source. The next push to `main` will publish the project page at the repository's GitHub Pages URL.

The hosted page deliberately reports the project as **Stage 0** and does not imply that KVDelta has established predictive ability. Later experiment jobs can replace `site/status.json` and add plots/results before the Pages artifact is deployed.
