from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
REQUIRED = [
    ROOT / "README.md",
    ROOT / "docs" / "DATA_SOURCES.md",
    ROOT / "docs" / "EXPERIMENT_001.md",
    ROOT / "docs" / "KVDELTA_CONTRACT.md",
]

missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.exists()]
if missing:
    raise SystemExit("Missing required project files: " + ", ".join(missing))

SITE.mkdir(parents=True, exist_ok=True)
status = {
    "project": "KVDelta Currents",
    "stage": "Stage 0: project definition",
    "predictive_claim_established": False,
    "experiment": "Experiment 001",
    "region": "North Pacific",
    "baselines": ["persistence", "climatology", "local linear trend"],
    "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
}
(SITE / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
print("site/status.json generated")
