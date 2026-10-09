import json
from pathlib import Path

from netCDF4 import Dataset, num2date
import numpy as np


ROOT = Path("artifacts/experiment-001")

FILES = {
    "west": ROOT / "noaa_np_west_2025-01.nc",
    "east": ROOT / "noaa_np_east_2025-01.nc",
}


def summarize(path: Path):
    with Dataset(path) as ds:
        time = ds.variables["time"][:]
        lat = ds.variables["latitude"][:]
        lon = ds.variables["longitude"][:]

        result = {
            "file": path.name,
            "bytes": path.stat().st_size,
            "dimensions": {
                name: len(dim)
                for name, dim in ds.dimensions.items()
            },
            "coordinates": {
                "time_count": len(time),
                "latitude_count": len(lat),
                "longitude_count": len(lon),
                "latitude_min": float(np.min(lat)),
                "latitude_max": float(np.max(lat)),
                "longitude_min": float(np.min(lon)),
                "longitude_max": float(np.max(lon)),
            },
            "variables": {},
        }

        time_var = ds.variables["time"]

        decoded_times = num2date(
            time[:],
            units=time_var.units,
            calendar=getattr(time_var, "calendar", "standard"),
        )
        
        iso_times = [
            t.strftime("%Y-%m-%dT%H:%M:%SZ")
            for t in decoded_times
        ]
        
        result["coordinates"]["timestamps"] = iso_times
        
        gaps_hours = []
        
        for previous, current in zip(decoded_times, decoded_times[1:]):
            delta = current - previous
            gaps_hours.append(delta.total_seconds() / 3600.0)
        
        result["coordinates"]["step_hours"] = gaps_hours
        result["coordinates"]["all_steps_24h"] = all(
            abs(hours - 24.0) < 1e-9
            for hours in gaps_hours
        )

        result["coordinates"]["time_start"] = iso_times[0]
        result["coordinates"]["time_end"] = iso_times[-1]

        result["coordinates"]["time_units"] = getattr(
            time_var, "units", None
        )

        for name in ("ugos", "vgos"):
            var = ds.variables[name]
            values = np.ma.array(var[:])

            valid = values.compressed()
            total_count = values.size
            valid_count = valid.size
            missing_count = total_count - valid_count

            result["variables"][name] = {
                "units": getattr(var, "units", None),
                "shape": list(values.shape),
                "total_count": int(total_count),
                "valid_count": int(valid_count),
                "missing_count": int(missing_count),
                "missing_fraction": (
                    float(missing_count / total_count)
                    if total_count
                    else None
                ),
                "min": float(valid.min()) if valid_count else None,
                "max": float(valid.max()) if valid_count else None,
            }

        return result


inspection = {
    "experiment": "001",
    "purpose": "raw acquisition inspection before K0/V construction",
    "transformations_applied": [],
    "files": {
        name: summarize(path)
        for name, path in FILES.items()
    },
}

west = inspection["files"]["west"]["coordinates"]
east = inspection["files"]["east"]["coordinates"]

inspection["dateline_check"] = {
    "west_max_longitude": west["longitude_max"],
    "east_min_longitude": east["longitude_min"],
    "native_coordinate_system_preserved": True,
}

output = ROOT / "inspection.json"

with output.open("w") as f:
    json.dump(inspection, f, indent=2, sort_keys=True)
    f.write("\n")

print(json.dumps(inspection, indent=2, sort_keys=True))
