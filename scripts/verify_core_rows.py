"""Replay every saved finalist under its exact winning policy.

Usage: python scripts/verify_core_rows.py REPO OUTPUT_JSON
Covers the core-item cells, the Top builds and every build style, each with the champion's rune
page (and the style's keystone). Run for baseline and candidate repositories, then compare rows
exactly. This does not rerun the bounded searches or establish global optimality.
"""

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
sys.path[:0] = [str(root), str(root / "tests")]
from sharpwr import engine_namespace, profiles_by_target
from sharpwr.core_items import cell_evaluator

ns = engine_namespace()
profiles = profiles_by_target()
payload = json.loads((root / "data/champion-core-items.json").read_text())
output, warnings, count = {}, {}, 0


def replay(name, section, cells, keystone=None):
    global count
    for key, cell in cells.items():
        evaluator = cell_evaluator(ns, profiles, name, cell["level"], cell["target"], keystone=keystone)
        for index, row in enumerate(cell["search"]["full"]):
            trace = evaluator.replay_row(row)
            count += 1
            warnings[name].update(trace.assumptions)
            output[f"{name}/{section}/{key}/{index}"] = {
                "damage": trace.total_damage,
                "ttk": trace.killed_at,
                "remaining": trace.hp_remaining,
                "hits": [(x["time"], x["action"], x["damage"]) for x in trace.log],
            }


for name, record in payload["champions"].items():
    warnings[name] = set()
    replay(name, "core", record["cells"])
    replay(name, "top", record.get("top", {}))
    for style in record.get("styles", []):
        replay(name, f"style:{style['key']}", style["cells"], style["keystone"])
    print(name, count, flush=True)
Path(sys.argv[2]).write_text(
    json.dumps(
        {"count": count, "rows": output, "warnings": {k: sorted(v) for k, v in warnings.items()}},
        separators=(",", ":"),
    )
)
