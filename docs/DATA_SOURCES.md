# Data sources

## Copernicus Marine — Global surface currents

Product: Global Total (COPERNICUS-GLOBCURRENT), Ekman and Geostrophic currents at the Surface and 15m.

Useful characteristics:

- global coverage
- 0.25° grid
- hourly, daily and monthly products
- multi-year coverage beginning in 1993
- near-real-time product available
- accessible through the Copernicus Marine Toolbox / Python API and file services

Product ID family: `MULTIOBS_GLO_PHY_MYNRT_015_003`

## Copernicus Marine — In-situ current observations

Product: Global Ocean in-situ near-real-time observations of ocean currents.

Includes:

- drifting-buoy near-surface velocities
- Argo-derived velocities
- HF-radar current observations
- eastward / northward velocity components
- temperature and associated quality/metadata fields

Product ID: `INSITU_GLO_PHY_UV_DISCRETE_NRT_013_048`

This is valuable as an independent observational check against gridded products.

## Copernicus Marine — Global ocean physics reanalysis

Product ID family: `GLOBAL_MULTIYEAR_PHY_001_030`

Useful for adding broader K variables such as temperature, salinity, sea-surface height, depth-dependent currents and other physical context.

## Data policy

Do not commit bulk NetCDF files to GitHub.

For each experiment, record:

- exact product ID
- dataset ID
- requested bounding box
- requested time range
- variables
- retrieval date
- source version if available
- checksum of the downloaded subset
- provider citation and licence
