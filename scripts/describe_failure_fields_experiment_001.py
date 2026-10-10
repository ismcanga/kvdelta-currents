import json
from math import sqrt
from pathlib import Path


ROOT = Path("artifacts/experiment-001")

INPUT = ROOT / "failure_localization_site.json"
OUTPUT = ROOT / "failure_field_descriptions.json"

GRID_SPACING_DEGREES = 0.25

# Approximate metres per degree latitude.
METRES_PER_DEGREE = 111_320.0

# For this first pass we use one fixed nominal spacing.
# This is intentionally simple and transparent.
DX_METRES = GRID_SPACING_DEGREES * METRES_PER_DEGREE
DY_METRES = GRID_SPACING_DEGREES * METRES_PER_DEGREE


def mean(values):
    if not values:
        return None

    return sum(values) / len(values)


def population_std(values):
    if not values:
        return None

    avg = mean(values)

    variance = sum(
        (value - avg) ** 2
        for value in values
    ) / len(values)

    return sqrt(variance)


def magnitude(u, v):
    return sqrt(u * u + v * v)


def flatten_valid(u_grid, v_grid):
    vectors = []

    for row_index in range(len(u_grid)):
        for column_index in range(len(u_grid[row_index])):
            u = u_grid[row_index][column_index]
            v = v_grid[row_index][column_index]

            if u is None or v is None:
                continue

            vectors.append((float(u), float(v)))

    return vectors


def vector_coherence(vectors):
    """
    0 means the vectors largely cancel.
    1 means they point together.

    This is a geometric descriptor only.
    """

    if not vectors:
        return None

    mean_u = mean([u for u, _ in vectors])
    mean_v = mean([v for _, v in vectors])

    mean_vector_speed = magnitude(
        mean_u,
        mean_v,
    )

    mean_individual_speed = mean(
        [
            magnitude(u, v)
            for u, v in vectors
        ]
    )

    if mean_individual_speed == 0:
        return 0.0

    return mean_vector_speed / mean_individual_speed


def center_difference(left, right, spacing):
    if left is None or right is None:
        return None

    return (right - left) / (2.0 * spacing)


def local_derivatives(u_grid, v_grid):
    """
    Estimate derivatives at the center cell of a 3x3 field.

    Grid orientation:

        row 0 = south
        row 1 = center latitude
        row 2 = north

        col 0 = west
        col 1 = center longitude
        col 2 = east

    divergence:
        du/dx + dv/dy

    vertical vorticity:
        dv/dx - du/dy

    These are simple centered finite differences.
    """

    if len(u_grid) != 3 or len(v_grid) != 3:
        return {
            "divergence_per_s": None,
            "vorticity_per_s": None,
        }

    if any(
        len(row) != 3
        for row in u_grid + v_grid
    ):
        return {
            "divergence_per_s": None,
            "vorticity_per_s": None,
        }

    west_u = u_grid[1][0]
    east_u = u_grid[1][2]

    south_v = v_grid[0][1]
    north_v = v_grid[2][1]

    west_v = v_grid[1][0]
    east_v = v_grid[1][2]

    south_u = u_grid[0][1]
    north_u = u_grid[2][1]

    du_dx = center_difference(
        west_u,
        east_u,
        DX_METRES,
    )

    dv_dy = center_difference(
        south_v,
        north_v,
        DY_METRES,
    )

    dv_dx = center_difference(
        west_v,
        east_v,
        DX_METRES,
    )

    du_dy = center_difference(
        south_u,
        north_u,
        DY_METRES,
    )

    divergence = None
    if du_dx is not None and dv_dy is not None:
        divergence = du_dx + dv_dy

    vorticity = None
    if dv_dx is not None and du_dy is not None:
        vorticity = dv_dx - du_dy

    return {
        "divergence_per_s": divergence,
        "vorticity_per_s": vorticity,
    }


def describe_frame(frame):
    u_grid = frame["ugos_mps"]
    v_grid = frame["vgos_mps"]

    vectors = flatten_valid(
        u_grid,
        v_grid,
    )

    speeds = [
        magnitude(u, v)
        for u, v in vectors
    ]

    mean_u = mean(
        [u for u, _ in vectors]
    )

    mean_v = mean(
        [v for _, v in vectors]
    )

    derivatives = local_derivatives(
        u_grid,
        v_grid,
    )

    return {
        "timestamp": frame["timestamp"],
        "step": frame["step"],
        "role": frame.get("role"),
        "valid_cell_count": len(vectors),
        "mean_u_mps": mean_u,
        "mean_v_mps": mean_v,
        "mean_speed_mps": mean(speeds),
        "speed_spread_mps": population_std(speeds),
        "vector_coherence": vector_coherence(vectors),
        "divergence_per_s": derivatives[
            "divergence_per_s"
        ],
        "vorticity_per_s": derivatives[
            "vorticity_per_s"
        ],
    }


def clean_number(value):
    if value is None:
        return None

    return round(float(value), 8)


def clean_frame(frame):
    cleaned = {}

    for key, value in frame.items():
        if isinstance(value, float):
            cleaned[key] = clean_number(value)
        else:
            cleaned[key] = value

    return cleaned


def describe_failure(failure):
    frames = [
        clean_frame(
            describe_frame(frame)
        )
        for frame in failure[
            "measurement_window"
        ]["frames"]
    ]

    return {
        "slice": failure["slice"],
        "rank": failure["rank"],
        "start": failure["start"],
        "end": failure["end"],
        "latitude": failure["latitude"],
        "longitude": failure["longitude"],
        "persistence_vector_miss_mps": (
            failure[
                "persistence_vector_miss_mps"
            ]
        ),
        "frames": frames,
    }


def main():
    if not INPUT.exists():
        raise SystemExit(
            f"Missing input artifact: {INPUT}"
        )

    data = json.loads(
        INPUT.read_text(
            encoding="utf-8"
        )
    )

    failures = [
        describe_failure(failure)
        for failure in data["failures"]
    ]

    output = {
        "experiment": "001",
        "source_artifact": INPUT.name,
        "purpose": (
            "describe the local measured vector field "
            "around selected failed calculations"
        ),
        "interpretation_rule": (
            "these descriptors summarize measured field "
            "behaviour. They do not identify cause or Delta."
        ),
        "descriptors": {
            "mean_u_mps": (
                "mean eastward measured velocity"
            ),
            "mean_v_mps": (
                "mean northward measured velocity"
            ),
            "mean_speed_mps": (
                "mean speed across valid cells"
            ),
            "speed_spread_mps": (
                "population standard deviation of "
                "cell speeds"
            ),
            "vector_coherence": (
                "magnitude of mean vector divided by "
                "mean vector magnitude; 0 to 1"
            ),
            "divergence_per_s": (
                "centered finite-difference estimate "
                "of du/dx + dv/dy"
            ),
            "vorticity_per_s": (
                "centered finite-difference estimate "
                "of dv/dx - du/dy"
            ),
        },
        "assumptions": {
            "grid_spacing_degrees": (
                GRID_SPACING_DEGREES
            ),
            "metres_per_degree": (
                METRES_PER_DEGREE
            ),
            "dx_metres": DX_METRES,
            "dy_metres": DY_METRES,
            "derivative_method": (
                "centered difference over the 3x3 field"
            ),
        },
        "failures": failures,
    }

    OUTPUT.write_text(
        json.dumps(
            output,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "experiment": "001",
                "source": INPUT.name,
                "output": OUTPUT.name,
                "failure_count": len(failures),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
