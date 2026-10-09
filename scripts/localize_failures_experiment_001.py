import json
from pathlib import Path

import numpy as np
from netCDF4 import Dataset, num2date


ROOT = Path("artifacts/experiment-001")

FILES = {
    "west": ROOT / "noaa_np_west_2025-01.nc",
    "east": ROOT / "noaa_np_east_2025-01.nc",
}

OUTPUT = ROOT / "failure_localization.json"

REQUIRED_INTERVAL_HOURS = 24.0
TOP_N_PER_SLICE = 100
NEIGHBOR_RADIUS = 1


def load_times(ds):
    time_var = ds.variables["time"]

    return list(
        num2date(
            time_var[:],
            units=time_var.units,
            calendar=getattr(time_var, "calendar", "standard"),
        )
    )


def direction_deg(u, v):
    angle = np.degrees(np.arctan2(v, u))
    return float((angle + 360.0) % 360.0)


def vector_error(u0, v0, u1, v1):
    return float(
        np.sqrt(
            (u1 - u0) ** 2
            + (v1 - v0) ** 2
        )
    )


def speed(u, v):
    return float(np.sqrt(u * u + v * v))


def neighbor_context(
    ugos,
    vgos,
    time_index,
    lat_index,
    lon_index,
):
    lat_start = max(0, lat_index - NEIGHBOR_RADIUS)
    lat_end = min(
        ugos.shape[1],
        lat_index + NEIGHBOR_RADIUS + 1,
    )

    lon_start = max(0, lon_index - NEIGHBOR_RADIUS)
    lon_end = min(
        ugos.shape[2],
        lon_index + NEIGHBOR_RADIUS + 1,
    )

    records = []

    for yi in range(lat_start, lat_end):
        for xi in range(lon_start, lon_end):
            if yi == lat_index and xi == lon_index:
                continue

            u0 = ugos[time_index, yi, xi]
            v0 = vgos[time_index, yi, xi]
            u1 = ugos[time_index + 1, yi, xi]
            v1 = vgos[time_index + 1, yi, xi]

            if (
                np.ma.is_masked(u0)
                or np.ma.is_masked(v0)
                or np.ma.is_masked(u1)
                or np.ma.is_masked(v1)
            ):
                records.append(
                    {
                        "lat_index": yi,
                        "lon_index": xi,
                        "valid": False,
                    }
                )
                continue

            records.append(
                {
                    "lat_index": yi,
                    "lon_index": xi,
                    "valid": True,
                    "vector_error_mps": vector_error(
                        float(u0),
                        float(v0),
                        float(u1),
                        float(v1),
                    ),
                }
            )

    valid_errors = [
        r["vector_error_mps"]
        for r in records
        if r.get("valid")
    ]

    if valid_errors:
        summary = {
            "valid_neighbor_count": len(valid_errors),
            "mean_vector_error_mps": float(
                np.mean(valid_errors)
            ),
            "median_vector_error_mps": float(
                np.median(valid_errors)
            ),
            "max_vector_error_mps": float(
                np.max(valid_errors)
            ),
        }
    else:
        summary = {
            "valid_neighbor_count": 0,
            "mean_vector_error_mps": None,
            "median_vector_error_mps": None,
            "max_vector_error_mps": None,
        }

    return {
        "radius_cells": NEIGHBOR_RADIUS,
        "summary": summary,
        "neighbors": records,
    }


def collect_slice(path: Path):
    with Dataset(path) as ds:
        times = load_times(ds)

        lats = np.asarray(
            ds.variables["latitude"][:],
            dtype=np.float64,
        )

        lons = np.asarray(
            ds.variables["longitude"][:],
            dtype=np.float64,
        )

        ugos = np.ma.array(ds.variables["ugos"][:])
        vgos = np.ma.array(ds.variables["vgos"][:])

        failures = []

        for time_index in range(len(times) - 1):
            start = times[time_index]
            end = times[time_index + 1]

            hours = (
                end - start
            ).total_seconds() / 3600.0

            if abs(hours - REQUIRED_INTERVAL_HOURS) > 1e-9:
                continue

            u0 = np.ma.array(ugos[time_index])
            v0 = np.ma.array(vgos[time_index])

            u1 = np.ma.array(ugos[time_index + 1])
            v1 = np.ma.array(vgos[time_index + 1])

            missing = (
                np.ma.getmaskarray(u0)
                | np.ma.getmaskarray(v0)
                | np.ma.getmaskarray(u1)
                | np.ma.getmaskarray(v1)
            )

            valid = ~missing

            if not np.any(valid):
                continue

            error = np.full(
                u0.shape,
                np.nan,
                dtype=np.float64,
            )

            error[valid] = np.sqrt(
                (
                    np.asarray(
                        u1[valid],
                        dtype=np.float64,
                    )
                    - np.asarray(
                        u0[valid],
                        dtype=np.float64,
                    )
                ) ** 2
                + (
                    np.asarray(
                        v1[valid],
                        dtype=np.float64,
                    )
                    - np.asarray(
                        v0[valid],
                        dtype=np.float64,
                    )
                ) ** 2
            )

            flat_indices = np.flatnonzero(
                np.isfinite(error)
            )

            for flat_index in flat_indices:
                yi, xi = np.unravel_index(
                    flat_index,
                    error.shape,
                )

                current_u = float(u0[yi, xi])
                current_v = float(v0[yi, xi])

                future_u = float(u1[yi, xi])
                future_v = float(v1[yi, xi])

                failures.append(
                    {
                        "start": start.strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        "end": end.strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        "time_index": time_index,
                        "lat_index": int(yi),
                        "lon_index": int(xi),
                        "latitude": float(lats[yi]),
                        "longitude": float(lons[xi]),
                        "K": {
                            "ugos_mps": current_u,
                            "vgos_mps": current_v,
                            "speed_mps": speed(
                                current_u,
                                current_v,
                            ),
                            "direction_deg": direction_deg(
                                current_u,
                                current_v,
                            ),
                        },
                        "V": {
                            "ugos_mps": future_u,
                            "vgos_mps": future_v,
                            "speed_mps": speed(
                                future_u,
                                future_v,
                            ),
                            "direction_deg": direction_deg(
                                future_u,
                                future_v,
                            ),
                        },
                        "vector_error_mps": vector_error(
                            current_u,
                            current_v,
                            future_u,
                            future_v,
                        ),
                        "speed_error_mps": abs(
                            speed(future_u, future_v)
                            - speed(current_u, current_v)
                        ),
                    }
                )

        failures.sort(
            key=lambda x: x["vector_error_mps"],
            reverse=True,
        )

        top = failures[:TOP_N_PER_SLICE]

        for item in top:
            item["neighbor_context"] = neighbor_context(
                ugos,
                vgos,
                item["time_index"],
                item["lat_index"],
                item["lon_index"],
            )

        return {
            "file": path.name,
            "top_n": len(top),
            "ranking_metric": "vector_error_mps",
            "failures": top,
        }


slices = {
    name: collect_slice(path)
    for name, path in FILES.items()
}

summary = {
    "experiment": "001",
    "purpose": (
        "localize the largest 24-hour persistence failures "
        "without discarding or explaining them"
    ),
    "selection": {
        "top_n_per_slice": TOP_N_PER_SLICE,
        "ranking_metric": "vector_error_mps",
        "required_interval_hours": REQUIRED_INTERVAL_HOURS,
    },
    "neighbor_context": {
        "radius_cells": NEIGHBOR_RADIUS,
        "meaning": (
            "3x3 neighborhood around the failure cell, "
            "excluding the center cell"
        ),
    },
    "interpretation_rule": (
        "large error is treated as a reconnaissance lead, "
        "not as Delta and not as an outlier to remove"
    ),
    "transformations_applied": [],
    "slices": slices,
}

with OUTPUT.open("w") as f:
    json.dump(summary, f, indent=2, sort_keys=True)
    f.write("\n")

print(
    json.dumps(
        {
            "experiment": summary["experiment"],
            "purpose": summary["purpose"],
            "selection": summary["selection"],
            "top_counts": {
                name: item["top_n"]
                for name, item in slices.items()
            },
            "top_failures": {
                name: (
                    item["failures"][:5]
                    if item["failures"]
                    else []
                )
                for name, item in slices.items()
            },
        },
        indent=2,
        sort_keys=True,
    )
)
