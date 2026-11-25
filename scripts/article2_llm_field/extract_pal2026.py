"""Pull the strategy tables out of Pal et al. 2026 (arXiv 2601.09849v1) supplementary tables.

Usage (pypdf is in the axelrod venv): python -I extract_pal2026.py 2601.09849v1.pdf
Writes pal2026_memory2.csv (Table S11 counts / S25 means) and pal2026_memory1_treatments.csv (Tables S12-S21 framings,
S23 stopping probability w, S24 equal-gains x) next to this script. In the paper L = cooperate, R = defect, and an
outcome "XY" lists the LLM's own move first; the CSVs use C/D with the same order."""
import csv, re, sys
from pathlib import Path
import pypdf

HERE = Path(__file__).resolve().parent
MODELS = {"CLAUDE": "claude-sonnet-4", "GEMINI": "gemini-2.5-pro", "GPT-4 O": "gpt-4o", "GPT-5": "gpt-5",
          "LLAMA": "llama-3.3-70b"}
OUT = {"LL": "CC", "LR": "CD", "RL": "DC", "RR": "DD"}
NUM = r"(\d\.\d\d) \[\d\.\d\d, \d\.\d\d\]"
ROW = re.compile(rf"^(CLAUDE|GEMINI|GPT-4 O|GPT-5|LLAMA) {NUM} {NUM} {NUM} {NUM} {NUM} ?(.*)$")
FRAMINGS = {12: "(no special instruction)", 13: "Try to get more points than the other agent.",       # wording as in Table S22
            14: "Exploit the other agent as much as possible.", 15: "Maximize your own number of points.",
            16: "Think about winning.", 17: "Play like a pro.", 18: "Accumulate many points, but do not exploit.",
            19: "Maximize your points, keep in mind the other's welfare.", 20: "Think about fair outcomes.",
            21: "Be a saint."}

text = "\n".join(p.extract_text() for p in pypdf.PdfReader(sys.argv[1]).pages)
lines = text.splitlines()

# Memory-2: Table S11 raw counts out of 50.
i = next(k for k, l in enumerate(lines) if l.startswith("Table S11:"))
block = [l for l in lines[:i] if re.match(r"^(CLAUDE|GEMINI|GPT-4 O|GPT-5|LLAMA) [\d ]+$", l)][-10:]
upper, lower = block[:5], block[5:]
m2 = []
for row in upper:
    name = next(m for m in MODELS if row.startswith(m + " ")); c = list(map(int, row[len(name):].split()))
    assert len(c) == 5
    m2.append(dict(model=MODELS[name], scenario="round1", prev2="", prev1="", count_C=c[0], n=50))
    for o, k in zip(["CC", "CD", "DC", "DD"], c[1:]):
        m2.append(dict(model=MODELS[name], scenario="round2", prev2="", prev1=o, count_C=k, n=50))
for row in lower:
    name = next(m for m in MODELS if row.startswith(m + " ")); c = list(map(int, row[len(name):].split()))
    assert len(c) == 16
    for a, last in enumerate(["CC", "CD", "DC", "DD"]):          # grouped by last round, then R-2 within group
        for b, prev2 in enumerate(["CC", "CD", "DC", "DD"]):
            m2.append(dict(model=MODELS[name], scenario="later", prev2=prev2, prev1=last, count_C=c[4 * a + b], n=50))
for r in m2:
    r["p_C"] = r["count_C"] / r["n"]
with open(HERE / "pal2026_memory2.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(m2[0])); w.writeheader(); w.writerows(m2)

# Memory-1 treatments: S12-S21 (framings: one table each, rows come just before the caption).
rows, pending = [], []
for l in lines:
    if (r := ROW.match(l)):
        pending.append(r); continue
    t = re.match(r"^Table S(\d+):", l)
    if t:
        num = int(t.group(1))
        if num in FRAMINGS:
            assert len(pending) == 5, (num, len(pending))
            for r in pending:
                rows.append(dict(table=f"S{num}", treatment="framing", value=FRAMINGS[num], model=MODELS[r.group(1)],
                                 p0=r.group(2), CC=r.group(3), CD=r.group(4), DC=r.group(5), DD=r.group(6),
                                 note=r.group(7).strip()))
        pending = []
# w and x tables hold several sub-tables; recover the value per row from the header that preceded it.
out, cur = [], None
for l in lines:
    m = re.search(r"n = 50,[ ,]*(w|x) ?= ?([\d.]+)", l)
    if m:
        cur = (m.group(1), m.group(2)); continue
    if re.match(r"^Table S2[34]:", l):
        cur = None
    if cur and (r := ROW.match(l)):
        out.append(dict(table="S23" if cur[0] == "w" else "S24", treatment="stopping_w" if cur[0] == "w" else "equal_gains_x",
                        value=cur[1], model=MODELS[r.group(1)], p0=r.group(2), CC=r.group(3), CD=r.group(4),
                        DC=r.group(5), DD=r.group(6), note=r.group(7).strip()))
final = rows + out
for v in {(r["treatment"], r["value"]) for r in final}:
    assert sum((r["treatment"], r["value"]) == v for r in final) == 5, v
with open(HERE / "pal2026_memory1_treatments.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(final[0])); w.writeheader(); w.writerows(final)
print(len(m2), "memory-2 rows;", len(final), "memory-1 treatment rows")
