"""Shared look for the Article 2 figures, copied from Article 1 (scripts/article1_figures/sse_math_p.py, payoffs.py,
old_model_on_new.py): DejaVu Sans, white paper, ink text, blue = cooperate, orange = defect,
circle = cooperate, square = defect, Player 1 filled, Player 2 in outline.

The five LLM strategies get one identity colour each, kept the same in every figure. Blue and orange are left out
because they mean cooperate and defect. The set was checked with the dataviz skill's validate_palette.js
(--pairs all, light): it passes, with a CVD pair in the 6-8 band (magenta vs aqua) and three colours under 3:1
contrast, so every LLM mark is also drawn as a diamond and labelled by name in ink."""
import warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon

INK, INK2, MUTED, LINE, GRID = "#1b1b1b", "#3d3c39", "#6b6a66", "#c9c8c3", "#e6e5e1"
COOP, DEFECT, FIELD = "#2a78d6", "#eb6834", "#c9c8c3"

# name in the results files -> (short label, closest classic, colour)
LLMS = {
    "LLM: Llama 3.3 70B":   ("Llama 3.3 70B",   "close to Generous Tit for Tat", "#1baf7a"),
    "LLM: GPT-4o":          ("GPT-4o",          "GRIM",                          "#eda100"),
    "LLM: Claude Sonnet 4": ("Claude Sonnet 4", "Forgiver",                      "#6250d6"),
    "LLM: GPT-5":           ("GPT-5",           "between WSLS and Forgiver",     "#e87ba4"),
    "LLM: Gemini 2.5 Pro":  ("Gemini 2.5 Pro",  "close to Win-Stay Lose-Shift",  "#008300"),
}
TFT = "k92r"   # Tit for Tat: Anatol Rapoport's 1980 Fortran entry in Knight et al.'s field


def setup():
    plt.rcParams.update({"font.family": ["DejaVu Sans"], "savefig.facecolor": "white", "figure.facecolor": "white"})


def axes_style(ax):
    ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(LINE)
    ax.tick_params(colors=MUTED, labelsize=11)


def titles(fig, x, y, title, sub):
    fig.text(x, y, title, fontsize=16, fontweight="bold", color=INK, va="bottom")
    fig.text(x, y - 0.012, sub, fontsize=11, color=MUTED, linespacing=1.4, va="top")


def diamond(ax, x, y, r, color, **kw):
    """A strategy marker (diamonds, as in Article 1's strategy cube, so they are not read as moves)."""
    ax.add_patch(Polygon([(x, y + r), (x + r, y), (x, y - r), (x - r, y)], closed=True, facecolor=color,
                         edgecolor=kw.pop("edgecolor", "white"), lw=kw.pop("lw", 0), **kw))


def move(ax, x, y, mv, r, player, pt, lw=1.8):
    """Circle = cooperate, square = defect. Player 1 filled, Player 2 an ink outline (as in payoffs.py)."""
    if player == 2:
        r -= lw * pt / 2
        kw = dict(facecolor="white", edgecolor=INK, lw=lw, zorder=3)
    else:
        kw = dict(facecolor=COOP if mv == "C" else DEFECT, edgecolor="none", zorder=3)
    if mv == "C":
        ax.add_patch(Circle((x, y), r, **kw))
    else:
        s = 0.88 * r
        ax.add_patch(Rectangle((x - s, y - s), 2 * s, 2 * s, joinstyle="miter", **kw))
