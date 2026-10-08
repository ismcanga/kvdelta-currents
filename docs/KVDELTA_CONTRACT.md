# KVΔ experimental contract

KVΔ must be defined before a sealed evaluation period is opened.

For every experiment record:

- K: exactly which observable variables and constraints are available at prediction time.
- Δ: how the additional co-determining dimension is represented or inferred.
- V: exactly which future observable is predicted or explained.
- Horizon: t+n.
- Region and depth.
- Source datasets and versions.
- Baselines.
- Scoring functions.
- Any fitted parameters.

## Non-negotiable rule

Delta is not allowed to contain information unavailable at prediction time. If Δ is inferred from future V, the experiment is explanatory only and must not be labelled predictive.

## Falsification

A KVΔ formulation fails a stated experiment when it does not improve on declared baselines under the predeclared score, or when its apparent advantage does not reproduce on an independent interval/region.
