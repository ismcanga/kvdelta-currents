# Experiment 001 — Missing state in North Pacific surface currents

Status: design only.

## Aim

Start with a deliberately limited declaration of what is known, observe the later current state, and identify where and under what conditions K repeatedly fails to account for V.

The first objective is not to calculate Δ. It is to determine whether what K missed contains repeatable structure rather than only noise.

## Initial scope

* Region: North Pacific
* Depth: surface
* Cadence: daily first
* Primary horizon: 24 hours
* Secondary horizon: 72 hours
* Core observable: eastward and northward current velocity

The exact dataset, geographic bounds, historical interval, and resolution will be recorded before the first data run.

## K0 — initial known state

K0 contains only:

* latitude
* longitude
* timestamp
* eastward current velocity u(t)
* northward current velocity v(t)

Nothing else belongs in K0.

## V — resulting state

Primary V:

* u(t + 24 h)
* v(t + 24 h)

Derived observations may include:

* speed
* direction
* displacement of a virtual particle

The same experiment may subsequently be repeated at 72 hours.

## Δ

Δ means what K0 missed in accounting for V.

Δ is not defined as:

* V − K
* forecast error
* vector difference
* residual magnitude

Those measurements can reveal where K0 is inadequate, but they do not themselves identify Δ.

## First discovery pass

Observe where and when K0 fails.

Look for repeatable structure associated with:

* location
* season or time
* current speed
* turning
* spatial gradients
* geographic boundaries
* transitions between flow regimes

Do not add explanatory variables merely because they are available.

## Expansion

If a repeatable failure pattern suggests a missing factor, construct a new K containing a measurable representation of that candidate.

Possible later additions include:

* recent current history
* neighbouring current state
* spatial gradients
* wind forcing
* sea-surface temperature
* other physical context

These are candidates, not assumptions.

## Baselines

At minimum compare against:

* persistence
* seasonal/local climatology
* linear extrapolation

Baseline failures are useful evidence too.

## Evaluation

Use chronological:

1. discovery
2. validation
3. sealed test

Discovery may inspect V to search for missing structure.

Validation tests whether a candidate is worth retaining.

The sealed test is opened only after the revised K, parameters, metrics, and thresholds are fixed.

Evidence for a candidate Δ

A candidate missing factor gains support only if:

1. a repeatable failure pattern motivates it;
2. it can be represented without access to target V;
3. adding it to K improves validation performance;
4. that improvement survives the sealed test;
5. the effect reproduces on another interval or region.

## First deliverable

Publish:

* the exact K0
* exact V
* data source and provenance
* geographic bounds
* historical interval
* source resolution
* baseline results
* maps or summaries showing where K0 succeeds and fails

No claim that Δ has been identified should be made until repeatable missing structure has actually been demonstrated.
A more sophisticated baseline may be added later, but the first experiment should remain interpretable.

## Split

Use strictly chronological discovery, validation and sealed-test windows. Dates must be fixed before final model/formula tuning.

## Pass condition

No generic "works" label. Each metric gets a declared threshold and confidence interval. Reproduction on a second interval or region is required before any general claim.
