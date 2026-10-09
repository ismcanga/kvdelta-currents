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
SITE_OUTPUT = ROOT / "failure_localization_site.json"

REQUIRED_INTERVAL_HOURS = 24.0
TOP_N_PER_SLICE = 25

# Measurement support around a failed calculation.
SPATIAL_RADIUS = 1      # 3x3 grid
TIME_RADIUS = 2         # t-2 ... t+2

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


def measurement_window(
    times,
    lats,
    lons,
    ugos,
    vgos,
    failure_time_index,
    failure_lat_index,
    failure_lon_index,
):
    """
    Return the raw measurement set surrounding a failed calculation.

    This does not classify the failure and does not infer Delta.

    It preserves a small spatiotemporal window so later calculations
    can investigate what K failed to account for.
    """

    time_start = max(
        0,
        failure_time_index - TIME_RADIUS,
    )

    # +1 includes the V endpoint of the failed transition.
    time_end = min(
        len(times),
        failure_time_index + TIME_RADIUS + 1,
    )

    lat_start = max(
        0,
        failure_lat_index - SPATIAL_RADIUS,
    )

    lat_end = min(
        len(lats),
        failure_lat_index + SPATIAL_RADIUS + 1,
    )

    lon_start = max(
        0,
        failure_lon_index - SPATIAL_RADIUS,
    )

    lon_end = min(
        len(lons),
        failure_lon_index + SPATIAL_RADIUS + 1,
    )

    frames = []

    for ti in range(time_start, time_end):
        cells = []

        for yi in range(lat_start, lat_end):
            for xi in range(lon_start, lon_end):
                u = ugos[ti, yi, xi]
                v = vgos[ti, yi, xi]

                center = (
                    yi == failure_lat_index
                    and xi == failure_lon_index
                )

                if (
                    np.ma.is_masked(u)
                    or np.ma.is_masked(v)
                ):
                    cells.append(
                        {
                            "latitude": float(lats[yi]),
                            "longitude": float(lons[xi]),
                            "center": center,
                            "valid": False,
                        }
                    )
                    continue

                u = float(u)
                v = float(v)

                cells.append(
                    {
                        "latitude": float(lats[yi]),
                        "longitude": float(lons[xi]),
                        "center": center,
                        "valid": True,
                        "ugos_mps": u,
                        "vgos_mps": v,
                        "speed_mps": speed(u, v),
                        "direction_deg": direction_deg(u, v),
                    }
                )

        frames.append(
            {
                "timestamp": times[ti].strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "relative_measurement_index": (
                    ti - failure_time_index
                ),
                "is_calculation_start": (
                    ti == failure_time_index
                ),
                "is_subsequently_observed": (
                    ti == failure_time_index + 1
                ),
                "cells": cells,
            }
        )

    return {
        "spatial_radius_cells": SPATIAL_RADIUS,
        "time_radius_steps": TIME_RADIUS,
        "frames": frames,
    }

def compact_measurement_window(window):
    frames = window["frames"]

    if not frames:
        return {
            "latitudes": [],
            "longitudes": [],
            "frames": [],
        }

    first_cells = frames[0]["cells"]

    latitudes = list(
        dict.fromkeys(
            cell["latitude"]
            for cell in first_cells
        )
    )

    longitudes = list(
        dict.fromkeys(
            cell["longitude"]
            for cell in first_cells
        )
    )

    row_count = len(latitudes)
    column_count = len(longitudes)

    compact_frames = []

    for frame in frames:
        u_values = []
        v_values = []

        for cell in frame["cells"]:
            if cell["valid"]:
                u_values.append(cell["ugos_mps"])
                v_values.append(cell["vgos_mps"])
            else:
                u_values.append(None)
                v_values.append(None)

        u_rows = [
            u_values[i:i + column_count]
            for i in range(
                0,
                row_count * column_count,
                column_count,
            )
        ]

        v_rows = [
            v_values[i:i + column_count]
            for i in range(
                0,
                row_count * column_count,
                column_count,
            )
        ]

        compact_frame = {
            "timestamp": frame["timestamp"],
            "step": frame["relative_measurement_index"],
            "ugos_mps": u_rows,
            "vgos_mps": v_rows,
        }

        if frame["is_calculation_start"]:
            compact_frame["role"] = "calculation_start"

        if frame["is_subsequently_observed"]:
            compact_frame["role"] = "subsequently_observed"

        compact_frames.append(compact_frame)

    return {
        "latitudes": latitudes,
        "longitudes": longitudes,
        "frames": compact_frames,
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
                        "measurement_at_t": {
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
                        "measurement_at_t_plus_24h": {
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
                        "persistence_vector_miss_mps": vector_error(
                            current_u,
                            current_v,
                            future_u,
                            future_v,
                        ),
                        "persistence_speed_miss_mps": abs(
                            speed(future_u, future_v)
                            - speed(current_u, current_v)
                        ),
                    }
                )

        failures.sort(
            key=lambda x: x["persistence_vector_miss_mps"],
            reverse=True,
        )

        top = failures[:TOP_N_PER_SLICE]

        for item in top:
            item["measurement_window"] = measurement_window(
                times,
                lats,
                lons,
                ugos,
                vgos,
                item["time_index"],
                item["lat_index"],
                item["lon_index"],
            )
            
        return {
            "file": path.name,
            "top_n": len(top),
            "ranking_metric": "persistence_vector_miss_mps",
            "failures": top,
        }


slices = {
    name: collect_slice(path)
    for name, path in FILES.items()
}

summary = {
    "experiment": "001",
    "purpose": (
        "identify failed calculation steps and preserve "
        "the surrounding measurement set needed to investigate "
        "what calculation was missing"
    ),
    "selection": {
        "top_n_per_slice": TOP_N_PER_SLICE,
        "ranking_metric": "persistence_vector_miss_mps",
        "required_interval_hours": REQUIRED_INTERVAL_HOURS,
    },
    "measurement_support": {
        "spatial_radius_cells": SPATIAL_RADIUS,
        "time_radius_steps": TIME_RADIUS,
        "rule": (
            "preserve raw surrounding measurements around each "
            "selected failed calculation; do not infer cause or Delta"
        ),
    },
    "interpretation_rule": (
        "ranking only selects failed calculations for inspection. "
        "The surrounding measurement window is calculation support. "
        "Neither the error nor the measurement window is Delta."
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

site_failures = []

for slice_name, slice_data in slices.items():
    for rank, failure in enumerate(
        slice_data["failures"],
        start=1,
    ):
        site_failures.append(
            {
                "slice": slice_name,
                "rank": rank,
                "start": failure["start"],
                "end": failure["end"],
                "latitude": failure["latitude"],
                "longitude": failure["longitude"],
                "persistence_vector_miss_mps": (
                    failure["persistence_vector_miss_mps"]
                ),
                "measurement_at_t": (
                    failure["measurement_at_t"]
                ),
                "measurement_at_t_plus_24h": (
                    failure["measurement_at_t_plus_24h"]
                ),
                "measurement_window": compact_measurement_window(
                    failure["measurement_window"]
                ),
            }
        )

site_summary = {
    "experiment": "001",
    "source_artifact": "failure_localization.json",
    "purpose": "compact site projection of selected failed calculations",
    "cell_measurements": [
        "ugos_mps",
        "vgos_mps",
    ],
    "derived_for_display": [
        "speed_mps",
        "direction_deg",
    ],
    "failures": site_failures,
}

with SITE_OUTPUT.open("w") as f:
    json.dump(
        site_summary,
        f,
        separators=(",", ":"),
    )
    f.write("\n")

print(
    f"{SITE_OUTPUT} generated "
    f"({len(site_failures)} failures)"
)
