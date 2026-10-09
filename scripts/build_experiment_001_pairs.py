import json
from datetime import timedelta
from pathlib import Path

import numpy as np
from netCDF4 import Dataset, num2date


ROOT = Path("artifacts/experiment-001")

FILES = {
    "west": ROOT / "noaa_np_west_2025-01.nc",
    "east": ROOT / "noaa_np_east_2025-01.nc",
}

OUTPUT = ROOT / "pairs_summary.json"


def load_times(ds):
    time_var = ds.variables["time"]

    return list(
        num2date(
            time_var[:],
            units=time_var.units,
            calendar=getattr(time_var, "calendar", "standard"),
        )
    )


def summarize_pairs(path: Path):
    with Dataset(path) as ds:
        times = load_times(ds)

        ugos = np.ma.array(ds.variables["ugos"][:])
        vgos = np.ma.array(ds.variables["vgos"][:])

        lat_count = len(ds.dimensions["latitude"])
        lon_count = len(ds.dimensions["longitude"])
        grid_cells = lat_count * lon_count

        valid_intervals = 0
        rejected_non_24h_intervals = 0

        candidate_pairs = 0
        valid_pairs = 0
        rejected_missing_pairs = 0

        interval_records = []

        for index in range(len(times) - 1):
            start = times[index]
            end = times[index + 1]

            delta = end - start
            hours = delta.total_seconds() / 3600.0

            if abs(hours - 24.0) > 1e-9:
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

            valid_intervals += 1
            candidate_pairs += grid_cells

            u_now = np.ma.array(ugos[index])
            v_now = np.ma.array(vgos[index])

            u_future = np.ma.array(ugos[index + 1])
            v_future = np.ma.array(vgos[index + 1])

            missing = (
                np.ma.getmaskarray(u_now)
                | np.ma.getmaskarray(v_now)
                | np.ma.getmaskarray(u_future)
                | np.ma.getmaskarray(v_future)
            )

            missing_count = int(np.count_nonzero(missing))
            interval_valid_pairs = grid_cells - missing_count

            valid_pairs += interval_valid_pairs
            rejected_missing_pairs += missing_count

            interval_records.append(
                {
                    "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "hours": hours,
                    "accepted": True,
                    "grid_cells": grid_cells,
                    "valid_pairs": interval_valid_pairs,
                    "rejected_missing_pairs": missing_count,
                }
            )

        return {
            "file": path.name,
            "grid": {
                "latitude_count": lat_count,
                "longitude_count": lon_count,
                "grid_cells": grid_cells,
            },
            "time": {
                "observations": len(times),
                "candidate_adjacent_intervals": max(len(times) - 1, 0),
                "accepted_24h_intervals": valid_intervals,
                "rejected_non_24h_intervals": rejected_non_24h_intervals,
            },
            "pairs": {
                "candidate_pairs": candidate_pairs,
                "valid_pairs": valid_pairs,
                "rejected_missing_pairs": rejected_missing_pairs,
            },
            "intervals": interval_records,
        }


summary = {
    "experiment": "001",
    "purpose": "construct the valid population of K0 to V 24-hour pairs",
    "pair_definition": {
        "K0": [
            "latitude",
            "longitude",
            "timestamp",
            "ugos_t",
            "vgos_t",
        ],
        "V": [
            "ugos_t_plus_24h",
            "vgos_t_plus_24h",
        ],
        "required_interval_hours": 24,
        "missing_value_policy": "reject pair if any required velocity value is missing",
    },
    "transformations_applied": [],
    "slices": {
        name: summarize_pairs(path)
        for name, path in FILES.items()
    },
}

summary["totals"] = {
    "candidate_pairs": sum(
        item["pairs"]["candidate_pairs"]
        for item in summary["slices"].values()
    ),
    "valid_pairs": sum(
        item["pairs"]["valid_pairs"]
        for item in summary["slices"].values()
    ),
    "rejected_missing_pairs": sum(
        item["pairs"]["rejected_missing_pairs"]
        for item in summary["slices"].values()
    ),
}

with OUTPUT.open("w") as f:
    json.dump(summary, f, indent=2, sort_keys=True)
    f.write("\n")

print(json.dumps(summary, indent=2, sort_keys=True))
