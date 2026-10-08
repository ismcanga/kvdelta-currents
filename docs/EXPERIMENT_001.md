# Experiment 001 — North Pacific surface-current transition

Status: design only.

## Aim

Test whether a predeclared KVΔ representation improves short-horizon prediction of surface-current transitions over simple baselines.

## Initial scope

- Region: North Pacific
- Product: Copernicus global surface currents
- Depth: surface
- Resolution: 0.25°
- Cadence: daily first; hourly second
- Horizons: 1 day and 3 days
- Core observable: vector current (u, v)

## V candidates

Evaluate separately:

1. future u and v
2. future speed
3. future direction
4. virtual-particle displacement

## Required baselines

- persistence
- seasonal/local climatology
- linear extrapolation

A more sophisticated baseline may be added later, but the first experiment should remain interpretable.

## Split

Use strictly chronological discovery, validation and sealed-test windows. Dates must be fixed before final model/formula tuning.

## Pass condition

No generic "works" label. Each metric gets a declared threshold and confidence interval. Reproduction on a second interval or region is required before any general claim.
