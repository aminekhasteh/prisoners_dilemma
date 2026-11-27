"""Coverage of every Article 2 tournament run, read from the result files (no axelrod needed).

For each group (results folder) and condition it counts the seed x length tournaments that are in the
<condition>_per_tournament.csv files and compares them with the tournaments Knight et al. ran. Where the pairs/ folder
is present (it is not in git), it also counts the pair files that are complete, which shows a run in progress.

  python check_results.py            # table
  python check_results.py --json     # the same as JSON (make_tracker.py imports status() instead)
"""
import argparse, csv, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KNIGHT = [HERE.parent.parent / "Data/knight2026/src/data", Path.home() / "projects/prisoners_dilemma/Data/knight2026/src/data"]
FOLDERS = {"standard": "full_tournament", "noise1": "full_tournament_1_percent_noise",
           "noise5": "full_tournament_5_percent_noise"}
# Knight et al.'s seeds, used when the Knight data is not on this machine (checked against it on 2026-11-25).
SEEDS = {"standard": list(range(20)), "noise1": [0, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 19],
         "noise5": [2, 7, 10, 14, 15, 16, 18]}
# group -> (results folder, new pairs per tournament)
GROUPS = {"pal_m1": ("results", 1370), "pal_m2": ("results_m2", 1395), "new": ("results_new", 4335),
          "new_m3": ("results_m3", 3015)}
# tracker condition -> (runner condition, lengths)
CONDITIONS = {"standard 63": ("standard", [63]), "standard 77-308": ("standard", [77, 151, 156, 308]),
              "noise1": ("noise1", [63]), "noise5": ("noise5", [63])}


def knight_seeds(cond, turns):
    for base in KNIGHT:
        d = base / FOLDERS[cond]
        if d.exists():
            return sorted({int(m.group(1)) for f in d.glob(f"full_{turns}_turns_*_seed_summary.csv")
                           if (m := re.search(r"_(\d+)_seed_summary", f.name))})
    return SEEDS[cond]


def combined(folder, cond):
    """(turns, seed) pairs found in the per-tournament CSVs of one runner condition (250 repetitions only)."""
    got = set()
    for f in [folder / f"{cond}_per_tournament.csv"] + ([folder / "standard63_per_tournament.csv"] if cond == "standard" else []):
        if f.exists():
            got |= {(int(r["turns"]), int(r["seed"])) for r in csv.DictReader(open(f)) if r.get("reps", "250") == "250"}
    return got


def complete_pairs(folder, cond, turns, seed, want):
    """Distinct pairs in the pair file, or None when the pairs/ folder is not on this machine."""
    if not (folder / "pairs").exists():
        return None
    f = folder / "pairs" / f"{cond}_{turns}t_seed{seed}_250reps.jsonl"
    if not f.exists():
        return 0
    seen = set()
    for line in open(f):
        m = re.match(r'\{"i": (\d+), "j": (\d+)', line)
        if m and line.endswith("\n"):
            seen.add(m.groups())
    return len(seen)


def status(root=HERE):
    """{(group, tracker condition): dict(status, combined, expected, pairs_done, pairs_files, missing)}."""
    out = {}
    for g, (fold, want) in GROUPS.items():
        folder = Path(root) / fold
        for label, (cond, lengths) in CONDITIONS.items():
            expected = {(t, s) for t in lengths for s in knight_seeds(cond, t)}
            got = combined(folder, cond) & expected
            counts = [complete_pairs(folder, cond, t, s, want) for t, s in sorted(expected)]
            have_pairs = counts[0] is not None
            full = sum(c is not None and c >= want for c in counts)
            started = any(c for c in counts if c)
            if got == expected:
                st = "Done"
            elif got or started:
                st = "Running"
            else:
                st = "Not started"
            out[(g, label)] = dict(status=st, combined=len(got), expected=len(expected),
                                   pairs_done=full if have_pairs else None, missing=sorted(expected - got))
    return out


def cell(d):
    if d["status"] == "Done":
        return "Done"
    if d["status"] == "Not started":
        return "Not started"
    extra = f", {d['pairs_done']} with all pairs played" if d["pairs_done"] is not None else ""
    return f"Running ({d['combined']} of {d['expected']} combined{extra})"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", type=Path, default=HERE, help="folder holding results*/ (default: this script's)")
    args = ap.parse_args()
    st = status(args.root)
    if args.json:
        print(json.dumps({f"{g}|{c}": v for (g, c), v in st.items()}, indent=1))
        return
    print(f"{'group':8} {'condition':16} {'status':12} {'combined':>9} {'pairs done':>10}")
    for (g, c), d in st.items():
        print(f"{g:8} {c:16} {d['status']:12} {d['combined']:>4} / {d['expected']:<3} "
              f"{'' if d['pairs_done'] is None else d['pairs_done']:>10}")


if __name__ == "__main__":
    main()
