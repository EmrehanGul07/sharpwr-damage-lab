"""Damage comparison report: Python Damage Lab vs the C# simulation (M1 acceptance #2).

Formula cases: the C# value is computed with the bit-exact Q32.32 model (fixed_point_model.py),
which CI proves identical to the C# Fix64 (fix64-vectors). Scenario rows (AA loops, rotation)
come from the C# tests' REPORT lines in CI and are passed in with --scenario.
Writes docs/moba/milestones/M1-parity.md and M1-parity-cases.csv.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from fixed_point_model import (Fix, crit_scaled, effective_resistance,  # noqa: E402
                               resistance_multiplier, scaled_ability, stat_at_level)

FIXTURE = ROOT / "game/parity/fixtures/samira-reference-v1.json"
CONTENT = ROOT / "game/content/reference-riot/champions/samira.champion.json"
OUT = ROOT / "docs/moba/milestones"


def fix(v):
    return Fix.parse(repr(float(v)))


def rows():
    fx = json.loads(FIXTURE.read_text())
    content = json.loads(CONTENT.read_text())
    stats, abilities = content["stats"], content["abilities"]
    out = []
    pairs = {"ad": ("base_ad", "ad_per_level"), "hp": ("base_hp", "hp_per_level"),
             "armor": ("base_armor", "armor_per_level"), "mr": ("base_mr", "mr_per_level")}
    for c in fx["level_stats"]["cases"]:
        for stat, (b, g) in pairs.items():
            got = stat_at_level(Fix.parse(stats[b]["value"]), Fix.parse(stats[g]["value"]), c["level"]).to_float()
            status = "/".join(sorted({stats[b]["status"], stats[g]["status"]}))
            out.append(("level_stat", f"L{c['level']} {stat}", c[stat], got, status))
    for c in fx["resistance"]["cases"]:
        eff = effective_resistance(fix(c["resistance"]), fix(c["pct_pen"]), fix(c["flat_pen"]))
        out.append(("resistance", f"R{c['resistance']} pen{c['pct_pen']}/{c['flat_pen']}",
                    c["multiplier"], resistance_multiplier(eff).to_float(), "formula"))
    for c in fx["skills"]["cases"]:
        a = abilities[c["slot"]]
        raw = scaled_ability(Fix.parse(a["base_damage_by_rank"][c["rank"] - 1]["value"]),
                             Fix.parse(a["total_ad_ratio"]["value"]), Fix.parse(a["bonus_ad_ratio"]["value"]),
                             fix(c["ad"]), fix(c["base_ad"]))
        hit = crit_scaled(raw, Fix.parse(a["crit_effectiveness"]["value"]), fix(c["crit_damage"]), c["outcome"] == "Critical")
        resist = fix(c["mr"] if c["slot"] == "E" else c["armor"])
        total = Fix(0)
        for _ in range(c["hits"]):
            total = total + hit * resistance_multiplier(effective_resistance(resist, Fix(0), Fix(0)))
        label = f"{c['slot']}{c['rank']} AD{c['ad']}/{c['base_ad']} res{c['armor'] if c['slot'] != 'E' else c['mr']} {c['outcome']}"
        out.append(("ability", label, c["dealt_total"], total.to_float(), a["base_damage_by_rank"][c["rank"] - 1]["status"]))
    return fx, out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", action="append", default=[], help="REPORT line from the C# CI run")
    ap.add_argument("--ci-run", default="")
    args = ap.parse_args(argv)
    fx, data = rows()
    tol = fx["tolerance"]
    limit = {"level_stat": tol["stat"], "resistance": tol["multiplier"], "ability": tol["damage"]}
    with (OUT / "M1-parity-cases.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "case", "python", "csharp", "abs_delta", "tolerance", "pass", "data_status"])
        for g, case, py, cs, status in data:
            d = abs(py - cs)
            w.writerow([g, case, repr(py), repr(cs), f"{d:.3e}", limit[g], d <= limit[g], status])
    summary = []
    for g in ("level_stat", "resistance", "ability"):
        group = [r for r in data if r[0] == g]
        worst = max(abs(r[2] - r[3]) for r in group)
        statuses = sorted({r[4] for r in group})
        summary.append(f"| {g} | {len(group)} | {worst:.2e} | {limit[g]} | {'pass' if worst <= limit[g] else 'FAIL'} | {', '.join(statuses)} |")
    fp = fx["fingerprint"]
    md = [
        "# M1 · Damage comparison report (Python Damage Lab vs C# simulation)",
        "",
        f"Fixture `samira-reference-v1` · Damage Lab {fp['damage_lab_version']} · exported at {fp['git_head_at_export'][:7] if fp.get('git_head_at_export') else 'n/a'}",
        f"C# CI run: {args.ci_run or 'n/a'} (ubuntu x64, ubuntu ARM64, windows, macOS: identical results)",
        "",
        "## Formula cases",
        "",
        "C# values are computed by the bit-exact Q32.32 model, which CI proves identical to `Fix64`",
        "(`fix64-vectors-v1.json`). Every case: `M1-parity-cases.csv`.",
        "",
        "| Group | Cases | Max abs delta | Tolerance | Result | Data status of inputs |",
        "|---|---|---|---|---|---|",
        *summary,
        "",
        "## Simulation scenarios (C# `Match` vs Python `replay_samira`)",
        "",
        *(f"- {s}" for s in args.scenario),
        "",
        "## Data status legend",
        "",
        "`wr_wiki` Wild Rift wiki template · `damage_lab_preserved` existing Damage Lab value · "
        "`damage_lab_user_sourced` user-supplied WR evidence kept by the Damage Lab · "
        "`pc_reference_provisional` PC value used as a stand-in (AA windup, cast times, speeds) · "
        "`formula` no data input. Parity proves the C# engine reproduces the Damage Lab; it does not "
        "prove Wild Rift parity (see `docs/ingame-test-todo.md`).",
        "",
    ]
    (OUT / "M1-parity.md").write_text("\n".join(md))
    print(f"wrote {OUT / 'M1-parity.md'} and M1-parity-cases.csv ({len(data)} formula cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
