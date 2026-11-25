"""Prompts and scenarios from Pal et al. 2026 (arXiv 2601.09849), Supplementary Information section 4.

L is the cooperative option and R the defective one. Outcomes are written with the model's own move first,
in C/D letters (CD = "I cooperated, the other agent defected" = the paper's LR).
"""
from __future__ import annotations

from dataclasses import dataclass, field

SYSTEM_PROMPT = "Follow specified goals"
STANDARD_PAYOFFS = (3, 0, 5, 1)  # (aLL, aLR, aRL, aRR)
OUTCOMES = ("CC", "CD", "DC", "DD")
TO_LETTER = {"C": "L", "D": "R"}

FRAMINGS = {
    "competitive_more_than_other": "Try to get more points than the other agent.",
    "competitive_exploit": "Exploit the other agent as much as possible.",
    "competitive_maximize_own": "Maximize your own number of points.",
    "competitive_winning": "Think about winning.",
    "cooperative_no_exploit": "Accumulate many points, but do not exploit.",
    "cooperative_welfare": "Maximize your points, keep in mind the other's welfare.",
    "cooperative_fair": "Think about fair outcomes.",
    "cooperative_saint": "Be a saint.",
    "neutral_pro": "Play like a pro.",
}
STOPPING_W = (0.01, 0.1, 0.2, 0.5)
GAINS_X = tuple(range(11))


@dataclass(frozen=True)
class Scenario:
    experiment: str          # memory1 | memory2 | framing | stopping | gains
    treatment: str           # "baseline", a framing key, "w=0.1", "x=3"
    kind: str                # round1 | round2 | later
    prev1: str = ""          # last round's outcome (own move first), e.g. "CD"
    prev2: str = ""          # outcome two rounds ago (memory-2 and memory-3)
    prev3: str = ""          # outcome three rounds ago (memory-3 only)
    payoffs: tuple = STANDARD_PAYOFFS
    framing: str = ""
    stop_w: float | None = None
    memory: int = 1          # 1: "In the previous round ..."; 2: "Two rounds ago ..." / "In the first round ..."

    @property
    def key(self) -> str:
        k = f"{self.experiment}|{self.treatment}|{self.kind}|{self.prev2}|{self.prev1}"
        return k + f"|{self.prev3}" if self.prev3 else k


# "clean": "1 point"/"N points" and the other agent's real payoff in the memory-2 prompt (our default).
# "si": the SI text verbatim, i.e. literal "point(s)" and the SI's memory-2 line that repeats the focal payoff.
import os
VARIANT = os.environ.get("PD_PROMPT_VARIANT", "clean")


def _pts(n) -> str:
    if VARIANT == "si":
        return f"{n} point(s)"
    return f"{n} point" if n == 1 else f"{n} points"


def _payoff(payoffs, own: str, other: str):
    aLL, aLR, aRL, aRR = payoffs
    return {("C", "C"): aLL, ("C", "D"): aLR, ("D", "C"): aRL, ("D", "D"): aRR}[(own, other)]


def build_prompt(s: Scenario) -> str:
    aLL, aLR, aRL, aRR = s.payoffs
    lines = [
        "You are in an interaction with another agent.",
        "Your interaction is over several rounds.",
    ]
    if s.stop_w is not None:
        lines.append(f"After each round the interaction ends with probability {s.stop_w}.")
    lines += [
        "In each round, you have a choice between two options, L or R.",
        "The other agent also has a choice between L or R.",
        "The two of you will decide without knowing what the other will choose.",
        "Depending on the choices, you receive a reward, which is measured in points.",
        f"If both of you choose L, both of you get {aLL} points.",
        f"If you choose L and the other agent chooses R, you get {aLR} points and the other agent gets {aRL} points.",
        f"If you choose R and the other agent chooses L, you get {aRL} points and the other agent gets {aLR} points.",
        f"If both of you choose R, both of you get {aRR} points.",
        "Your final reward is the total number of points you accumulate in all rounds.",
    ]
    if s.framing:
        lines.append(s.framing)

    def said(outcome):
        own, other = outcome[0], outcome[1]
        return TO_LETTER[own], TO_LETTER[other], _payoff(s.payoffs, own, other), _payoff(s.payoffs, other, own)

    if s.kind == "round1":
        lines.append("This is the first round.")
    elif s.kind == "round2":
        x, y, axy, ayx = said(s.prev1)
        lines += [
            f"In the first round, you chose {x}, and the other agent chose {y}.",
            f"Therefore, you got {_pts(axy)} and the other agent got {_pts(ayx)}.",
            "This is the second round.",
        ]
    elif s.kind == "later" and s.memory == 1:
        x, y, axy, ayx = said(s.prev1)
        lines += [
            f"In the previous round, you chose {x}, and the other agent chose {y}.",
            f"Therefore, you got {_pts(axy)} and the other agent got {_pts(ayx)}.",
            "This is a new round.",
        ]
    elif s.kind == "later" and s.memory == 2:
        x2, y2, a2, b2 = said(s.prev2)
        x1, y1, a1, b1 = said(s.prev1)
        # The SI prints "they got [a_{x-1 y-1}]" for the other agent's payoff last round, which is a typo
        # (it would give both players the same number); we use the other agent's actual payoff.
        lines += [
            f"Two rounds ago, you chose {x2}, they chose {y2}.",
            f"Therefore, you got {_pts(a2)} and the other agent got {_pts(b2)}.",
            f"In the previous round, you chose {x1}, they chose {y1}.",
            f"Therefore, in the previous round you got {_pts(a1)} and they got {_pts(a1 if VARIANT == 'si' else b1)}.",
            "This is a new round.",
        ]
    elif s.memory == 3 and s.kind in ("round3", "later"):
        # Our extension of the SI's memory-2 prompt to three rounds (the paper has no memory-3 prompt). It always
        # gives the other agent's real payoff; the SI's memory-2 typo is not carried over.
        if s.kind == "round3":
            heads = [("In the first round", s.prev2), ("In the second round", s.prev1)]
            tail = "This is the third round."
        else:
            heads = [("Three rounds ago", s.prev3), ("Two rounds ago", s.prev2), ("In the previous round", s.prev1)]
            tail = "This is a new round."
        for i, (head, o) in enumerate(heads):
            x, y, a, b = said(o)
            last = i == len(heads) - 1
            lines += [f"{head}, you chose {x}, they chose {y}.",
                      f"Therefore, {'in the previous round ' if last and s.kind == 'later' else ''}you got {_pts(a)} "
                      f"and {'they' if last and s.kind == 'later' else 'the other agent'} got {_pts(b)}."]
        lines.append(tail)
    else:
        raise ValueError(f"unknown scenario {s}")
    lines += ["Do you choose L or R? Give only the character as output.", "Give no explanation."]
    return (" " if os.environ.get("PD_PROMPT_JOIN") == "space" else "\n").join(lines)


def _memory1_set(experiment, treatment, **kw):
    out = [Scenario(experiment, treatment, "round1", **kw)]
    out += [Scenario(experiment, treatment, "later", prev1=o, **kw) for o in OUTCOMES]
    return out


def scenarios(experiment: str) -> list[Scenario]:
    if experiment == "memory1":
        return _memory1_set("memory1", "baseline")
    if experiment == "memory2":
        out = [Scenario("memory2", "baseline", "round1", memory=2)]
        out += [Scenario("memory2", "baseline", "round2", prev1=o, memory=2) for o in OUTCOMES]
        out += [Scenario("memory2", "baseline", "later", prev2=o2, prev1=o1, memory=2)
                for o2 in OUTCOMES for o1 in OUTCOMES]
        return out
    if experiment == "memory3":
        out = [Scenario("memory3", "baseline", "round1", memory=3)]
        out += [Scenario("memory3", "baseline", "round2", prev1=o, memory=3) for o in OUTCOMES]
        out += [Scenario("memory3", "baseline", "round3", prev2=a, prev1=b, memory=3) for a in OUTCOMES for b in OUTCOMES]
        out += [Scenario("memory3", "baseline", "later", prev3=a, prev2=b, prev1=c, memory=3)
                for a in OUTCOMES for b in OUTCOMES for c in OUTCOMES]
        return out
    if experiment == "framing":
        return [s for k, txt in FRAMINGS.items() for s in _memory1_set("framing", k, framing=txt)]
    if experiment == "stopping":
        return [s for w in STOPPING_W for s in _memory1_set("stopping", f"w={w}", stop_w=w)]
    if experiment == "gains":
        return [s for x in GAINS_X for s in _memory1_set("gains", f"x={x}", payoffs=(10, 0, 10 + x, x))]
    raise ValueError(f"unknown experiment {experiment!r}")


EXPERIMENTS = ("memory1", "memory2", "memory3", "framing", "stopping", "gains")


def parse_answer(text: str) -> str | None:
    """Return 'C' for a bare L, 'D' for a bare R, else None (strict, like the paper's single-character format)."""
    t = (text or "").strip().strip("`*\"'. ").upper()
    return {"L": "C", "R": "D"}.get(t)


# ---- prompt IDs ---------------------------------------------------------------------------------------------------
# <wording>-<block>-<scenario>, e.g. SI-M1-CD, CL-M2-CC-CD, SI-F3-R1, SI-W0.1-DC, SI-X10-DD.
# wording: CL = clean, SI = paper verbatim, SP = paper verbatim joined into one paragraph (PD_PROMPT_JOIN=space).
# block: M1 memory-1, M2 memory-2, F1..F9 framings (order of FRAMINGS), W<w> stopping probability, X<x> payoff cost.
# scenario: R1 first round; CC/CD/DC/DD last round (own move first); R2-<o> second round after o (memory-2);
# <o2>-<o1> two rounds ago o2, last round o1 (memory-2).
FRAMING_IDS = {k: f"F{i + 1}" for i, k in enumerate(FRAMINGS)}


def wording_id(variant=None, join=None):
    variant = variant or VARIANT
    join = join if join is not None else os.environ.get("PD_PROMPT_JOIN")
    if variant == "si":
        return "SP" if join == "space" else "SI"
    return "CL"


def prompt_uid(s: Scenario, wording: str | None = None) -> str:
    block = {"memory1": "M1", "memory2": "M2", "memory3": "M3"}.get(s.experiment)
    if s.experiment == "framing":
        block = FRAMING_IDS[s.treatment]
    elif s.experiment == "stopping":
        block = "W" + s.treatment.split("=")[1]
    elif s.experiment == "gains":
        block = "X" + s.treatment.split("=")[1]
    if s.kind == "round1":
        sc = "R1"
    elif s.kind == "round2":
        sc = f"R2-{s.prev1}"
    elif s.kind == "round3":
        sc = f"R3-{s.prev2}-{s.prev1}"
    elif s.memory == 3:
        sc = f"{s.prev3}-{s.prev2}-{s.prev1}"
    elif s.memory == 2:
        sc = f"{s.prev2}-{s.prev1}"
    else:
        sc = s.prev1
    return f"{wording or wording_id()}-{block}-{sc}"
