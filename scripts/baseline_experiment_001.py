import json
import math
from pathlib import Path

import numpy as np
from netCDF4 import Dataset, num2date


ROOT = Path("artifacts/experiment-001")

FILES = {
    "west": ROOT / "noaa_np_west_2025-01.nc",
    "east": ROOT / "noaa_np_east_2025-01.nc",
}

OUTPUT = ROOT / "baseline_summary.json"

REQUIRED_INTERVAL_HOURS = 24.0

# Direction is unstable for nearly stationary flow.
# We keep those pairs for vector/speed metrics, but exclude them from
# direction-change statistics when either endpoint is below this speed.
DIRECTION_MIN_SPEED_MPS = 0.02


def load_times(ds):
    time_var = ds.variables["time"]

    return list(
        num2date(
            time_var[:],
            units=time_var.units,
            calendar=getattr(time_var, "calendar", "standard"),
        )
    )


def percentile(values, q):
    if values.size == 0:
        return None
    return float(np.percentile(values, q))


def metric_summary(values):
    values = np.asarray(values, dtype=np.float64)

    if values.size == 0:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "p90": None,
            "p95": None,
            "max": None,
        }

    return {
        "count": int(values.size),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "p90": percentile(values, 90),
        "p95": percentile(values, 95),
        "max": float(np.max(values)),
    }


def angular_difference_deg(u0, v0, u1, v1):
    """
    Smallest absolute angular difference between two vectors, in degrees.

    atan2(v, u) gives direction in radians.
    Result is folded into [0, 180].
    """

    a0 = np.arctan2(v0, u0)
    a1 = np.arctan2(v1, u1)

    diff = np.abs(a1 - a0)

    diff = np.where(
        diff > np.pi,
        (2.0 * np.pi) - diff,
        diff,
    )

    return np.degrees(diff)


def summarize_slice(path: Path):
    with Dataset(path) as ds:
        times = load_times(ds)

        ugos = np.ma.array(ds.variables["ugos"][:])
        vgos = np.ma.array(ds.variables["vgos"][:])

        vector_errors = []
        speed_errors = []
        direction_changes = []

        interval_records = []

        accepted_intervals = 0
        rejected_non_24h_intervals = 0

        total_valid_pairs = 0
        total_rejected_missing_pairs = 0
        total_direction_pairs = 0
        total_direction_rejected_low_speed = 0

        for index in range(len(times) - 1):
            start = times[index]
            end = times[index + 1]

            hours = (end - start).total_seconds() / 3600.0

            if abs(hours - REQUIRED_INTERVAL_HOURS) > 1e-9:
                rejected_non_24h_intervals += 1

                interval_records.append(
                    {
                        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "hours": hours,
                        "accepted": False,
                        "reason": "not_24_hours",
                    }
                )

                continue

            accepted_intervals += 1

            u0 = np.ma.array(ugos[index])
            v0 = np.ma.array(vgos[index])

            u1 = np.ma.array(ugos[index + 1])
            v1 = np.ma.array(vgos[index + 1])

            missing = (
                np.ma.getmaskarray(u0)
                | np.ma.getmaskarray(v0)
                | np.ma.getmaskarray(u1)
                | np.ma.getmaskarray(v1)
            )

            valid = ~missing

            valid_pairs = int(np.count_nonzero(valid))
            rejected_missing_pairs = int(np.count_nonzero(missing))

            total_valid_pairs += valid_pairs
            total_rejected_missing_pairs += rejected_missing_pairs

            if valid_pairs == 0:
                interval_records.append(
                    {
                        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "hours": hours,
                        "accepted": True,
                        "valid_pairs": 0,
                        "rejected_missing_pairs": rejected_missing_pairs,
                        "direction_pairs": 0,
                        "direction_rejected_low_speed": 0,
                    }
                )

                continue

            u0v = np.asarray(u0[valid], dtype=np.float64)
            v0v = np.asarray(v0[valid], dtype=np.float64)

            u1v = np.asarray(u1[valid], dtype=np.float64)
            v1v = np.asarray(v1[valid], dtype=np.float64)

            # Persistence baseline:
            # predicted future vector = current vector.
            vector_error = np.sqrt(
                (u1v - u0v) ** 2
                + (v1v - v0v) ** 2
            )

            speed0 = np.sqrt(u0v ** 2 + v0v ** 2)
            speed1 = np.sqrt(u1v ** 2 + v1v ** 2)

            speed_error = np.abs(speed1 - speed0)

            direction_valid = (
                (speed0 >= DIRECTION_MIN_SPEED_MPS)
                & (speed1 >= DIRECTION_MIN_SPEED_MPS)
            )

            direction_pair_count = int(
                np.count_nonzero(direction_valid)
            )

            direction_rejected_low_speed = (
                valid_pairs - direction_pair_count
            )

            total_direction_pairs += direction_pair_count
            total_direction_rejected_low_speed += (
                direction_rejected_low_speed
            )

            direction_change = angular_difference_deg(
                u0v[direction_valid],
                v0v[direction_valid],
                u1v[direction_valid],
                v1v[direction_valid],
            )

            vector_errors.append(vector_error)
            speed_errors.append(speed_error)

            if direction_change.size:
                direction_changes.append(direction_change)

            interval_records.append(
                {
                    "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "hours": hours,
                    "accepted": True,
                    "valid_pairs": valid_pairs,
                    "rejected_missing_pairs": rejected_missing_pairs,
                    "direction_pairs": direction_pair_count,
                    "direction_rejected_low_speed": (
                        direction_rejected_low_speed
                    ),
                    "metrics": {
                        "vector_error_mps": metric_summary(
                            vector_error
                        ),
                        "speed_error_mps": metric_summary(
                            speed_error
                        ),
                        "direction_change_deg": metric_summary(
                            direction_change
                        ),
                    },
                }
            )

        vector_errors = (
            np.concatenate(vector_errors)
            if vector_errors
            else np.array([], dtype=np.float64)
        )

        speed_errors = (
            np.concatenate(speed_errors)
            if speed_errors
            else np.array([], dtype=np.float64)
        )

        direction_changes = (
            np.concatenate(direction_changes)
            if direction_changes
            else np.array([], dtype=np.float64)
        )

        return {
            "file": path.name,
            "time": {
                "observations": len(times),
                "candidate_adjacent_intervals": max(
                    len(times) - 1,
                    0,
                ),
                "accepted_24h_intervals": accepted_intervals,
                "rejected_non_24h_intervals": (
                    rejected_non_24h_intervals
                ),
            },
            "pairs": {
                "valid_pairs": total_valid_pairs,
                "rejected_missing_pairs": (
                    total_rejected_missing_pairs
                ),
                "direction_pairs": total_direction_pairs,
                "direction_rejected_low_speed": (
                    total_direction_rejected_low_speed
                ),
            },
            "metrics": {
                "vector_error_mps": metric_summary(
                    vector_errors
                ),
                "speed_error_mps": metric_summary(
                    speed_errors
                ),
                "direction_change_deg": metric_summary(
                    direction_changes
                ),
            },
            "intervals": interval_records,
        }


slices = {
    name: summarize_slice(path)
    for name, path in FILES.items()
}


def combine_metric(metric_name):
    """
    Recompute combined summaries from interval-level statistics is not exact,
    so combined values are deliberately omitted here rather than approximated.
    Slice-level summaries remain exact.
    """

    return None


summary = {
    "experiment": "001",
    "baseline": {
        "name": "persistence",
        "prediction": {
            "ugos_t_plus_24h_hat": "ugos_t",
            "vgos_t_plus_24h_hat": "vgos_t",
        },
    },
    "purpose": (
        "measure where K0 persistence does and does not account "
        "for observed V at +24 hours"
    ),
    "direction_policy": {
        "minimum_speed_mps": DIRECTION_MIN_SPEED_MPS,
        "rule": (
            "direction change is reported only when speed at both "
            "K0 and V is at or above the threshold"
        ),
    },
    "missing_value_policy": (
        "reject pair if any required velocity value is missing"
    ),
    "required_interval_hours": REQUIRED_INTERVAL_HOURS,
    "transformations_applied": [],
    "slices": slices,
    "totals": {
        "valid_pairs": sum(
            item["pairs"]["valid_pairs"]
            for item in slices.values()
        ),
        "rejected_missing_pairs": sum(
            item["pairs"]["rejected_missing_pairs"]
            for item in slices.values()
        ),
        "direction_pairs": sum(
            item["pairs"]["direction_pairs"]
            for item in slices.values()
        ),
        "direction_rejected_low_speed": sum(
            item["pairs"]["direction_rejected_low_speed"]
            for item in slices.values()
        ),
    },
    "notes": [
        (
            "Vector and speed metrics include every valid K0/V pair."
        ),
        (
            "Direction statistics exclude only pairs below the declared "
            "minimum-speed threshold."
        ),
        (
            "No interpolation, smoothing, clipping, normalization, "
            "or Delta inference is performed."
        ),
        (
            "Combined east+west metric percentiles are intentionally "
            "not approximated from slice summaries."
        ),
    ],
}

with OUTPUT.open("w") as f:
    json.dump(summary, f, indent=2, sort_keys=True)
    f.write("\n")

print(json.dumps(summary, indent=2, sort_keys=True))
