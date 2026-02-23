"""Convert label_cache.jsonl to compact dandiset_assets.json for the viewer.

Keeps one asset per subject per dandiset (no cap on number of subjects).
"""

import json
import os
from collections import defaultdict
from pathlib import Path

LABEL_CACHE = Path(os.environ.get(
    "LABEL_CACHE",
    os.path.expanduser("~/dev/sandbox/analyze-locations/label_cache.jsonl"),
))
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "dandiset_assets.json"

FILTER_IDS = {997, 8}  # root, grey — not useful to display


def extract_subject(path):
    """Extract subject directory from asset path."""
    parts = path.split("/")
    return parts[0] if len(parts) > 1 else path.split("_")[0]


def main():
    # dandiset -> subject -> list of assets
    dandisets = defaultdict(lambda: defaultdict(list))

    with open(LABEL_CACHE) as f:
        for line in f:
            entry = json.loads(line)
            did = entry["dandiset_id"]
            asset_id = entry["asset_id"]
            path = entry["path"]
            matched = entry.get("matched_locations", {})

            regions = []
            for loc_key, matches in matched.items():
                for m in matches:
                    if m["id"] not in FILTER_IDS:
                        regions.append({
                            "id": m["id"],
                            "acronym": m["acronym"],
                            "name": m["name"],
                        })

            # Deduplicate by id
            seen = set()
            unique_regions = []
            for r in regions:
                if r["id"] not in seen:
                    seen.add(r["id"])
                    unique_regions.append(r)

            subject = extract_subject(path)
            dandisets[did][subject].append({
                "path": path,
                "asset_id": asset_id,
                "regions": unique_regions,
            })

    # Keep first asset per subject (sorted by path), no cap on subjects
    result = {}
    for did in sorted(dandisets):
        subjects = dandisets[did]
        assets = []
        for subj in sorted(subjects):
            # Pick the first asset (by path) for this subject
            sorted_assets = sorted(subjects[subj], key=lambda a: a["path"])
            assets.append(sorted_assets[0])
        result[did] = assets

    with open(OUTPUT, "w") as f:
        json.dump(result, f, separators=(",", ":"))

    total_assets = sum(len(v) for v in result.values())
    print(f"Wrote {OUTPUT}")
    print(f"  {len(result)} dandisets, {total_assets} assets (1 per subject)")


if __name__ == "__main__":
    main()
