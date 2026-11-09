"""Literal drawings for the home doors and the project views. Stdlib only.

Each drawing is a small exact diagram of the real work: the actual series for
Erdos #257, the R(f) = O(Q(f)^4) bound on log scales, two spin arrangements
that differ in half their spins, a paper sentence threaded to Lean, an agent
transcript with exit codes, the 10/6/0 run strip, 69% -> 77% on 58 problems,
page stacks drawn to scale (152 / 26 / 16 pages), and so on.

Shared visual language (styled in assets/door-art.css):
  * neutral structure (pages, panels, axes) in --quiet on --panel;
  * the meaningful part (the claim, the result, the changed line) in the
    area ink, via currentColor;
  * a two-strand plait thread joins the parts, after the Plectis mark.

Colour comes from CSS classes so both themes work; the page CSP forbids
inline style, so only SVG presentation attributes appear here. Font sizes are
presentation attributes in user units (the CSS never sets font-size on text,
which would override them).

Project drawings carry state classes read by the CSS:
  art-dim-<state>   fades the element while that demo state is active;
  art-hl-<state>    an ink halo, hidden except in that state;
  art-hide-<state>  hidden in that state.
"""
from __future__ import annotations

import math
import random
from html import escape as _escape

DOOR_KINDS = ["research", "proofs", "assistants", "explaining", "code", "testing"]
PROJECT_KINDS = [
    "maths", "quartic", "lean-exposition", "proof-reader", "atlas",
    "formal-verification", "agent-trace", "one-checkout", "safety-core",
    "codemap", "code-ontology-bridge", "zenith", "funnel", "narration-ir",
]

# (state_id, button label, caption). The first state is the initial one.
DEMO_STATES: dict[str, list[tuple[str, str, str]]] = {
    "maths": [
        ("question", "The question", "Is the sum of 1/(2ⁿ−1) over n in A irrational for every infinite A?"),
        ("proved", "Lean-checked", "Lean accepted: if the sum of 1/n over A is finite, it is irrational."),
        ("open", "Still open", "The general problem, for every infinite set A, is still open."),
    ],
    "quartic": [
        ("bound", "2020 bound", "For every total Boolean function, R(f) = O(Q(f)⁴)."),
        ("separation", "OpenAI's function", "A total function with R(f) = Q(f)^(4−o(1)): the exponent 4 cannot be lowered."),
        ("query", "One query", "A query is one look at one input bit: queries, not seconds."),
    ],
    "lean-exposition": [
        ("overlap", "Two near-best", "In large systems, two near-best arrangements differ in about half their spins."),
        ("couplings", "Couplings", "Each spin is +1 or −1; every pair has a random coupling."),
        ("count", "16 arrangements", "Four spins have 2⁴ = 16 arrangements; the long film scores each by hand."),
    ],
    "proof-reader": [
        ("sentence", "A sentence", "Click a sentence to open the five Lean lines it describes."),
        ("graph", "Dependencies", "A dependency graph of the Lean behind the proof."),
        ("axioms", "Axioms", "The axiom list, taken from Lean's own report."),
    ],
    "atlas": [
        ("map", "Subject map", "OpenAI's 719 maths papers, grouped into 372 families by subject."),
        ("paper", "One paper", "One paper about π, with its Lean statement."),
        ("verdicts", "Two checkers", "MathVet labels the statement full coverage; cert-machine labels it narrower."),
    ],
    "formal-verification": [
        ("components", "88 components", "88 Python components of one toolkit, one ring per kind of evidence."),
        ("dafny", "Dafny proofs", "Dafny proofs cover 16 calculations: 12 inside components, 4 shared."),
        ("coverage", "Whole claim", "Whole-claim coverage reads “unknown” for all 88 components."),
    ],
    "agent-trace": [
        ("fail", "Failing test", "The test command fails: exit code 1, with its saved output."),
        ("fix", "One-line fix", "The agent's edit changes one line."),
        ("pass", "Rerun", "The rerun passes: exit code 0."),
    ],
    "one-checkout": [
        ("result", "Result", "Agent A's patch is committed on top of the last commit."),
        ("before", "Before", "Agent B has unfinished staged and working-tree edits in the same file."),
        ("kept", "B's edits", "Agent B's staged and working-tree edits stay in place."),
    ],
    "safety-core": [
        ("build", "Rulebook", "One rulebook builds AGENTS.md, CLAUDE.md and Claude Code hooks."),
        ("written", "Written rule", "With a written rule, 6 of 10 runs still committed the made-up value."),
        ("hook", "Hook", "With a hook that checks the command, 0 of 10 runs did."),
    ],
    "codemap": [
        ("file", "File box", "Each file's box holds the docstring agents write under fixed headings."),
        ("callers", "Callers", "Each function links to the code that calls it."),
        ("text", "As text", "Coding agents can fetch the same descriptions as text."),
    ],
    "code-ontology-bridge": [
        ("tables", "Database", "Static analysis writes Python functions and calls into DuckDB."),
        ("query", "Recursive SQL", "Auto Ontology's text-to-SQL agent finds all callers with recursive SQL."),
        ("study", "Study", "With the database: 10.3 of 12 answered on average. DeepSeek alone: 3.2."),
    ],
    "zenith": [
        ("records", "Missed bugs", "Records of the bugs its test inputs missed on 28 practice problems."),
        ("result", "Held-out", "On 58 held-out problems: 77% of bugs caught, up from 69%."),
        ("timeouts", "Timeouts", "About half of the rise came from timeouts."),
    ],
    "funnel": [
        ("proof", "Lean proof", "One Lean-accepted proof, for Erdős #257, is the starting point."),
        ("pages", "Papers", "AI writes a 152-page record, a 26-page paper and a 16-page exposition."),
        ("video", "Video", "The same proof also becomes a video."),
    ],
    "narration-ir": [
        ("plan", "Plan", "Each spoken sentence gets a plan before animation code is written."),
        ("cue", "Word cue", "A named recorded word times the change: the third arrow turns on."),
        ("quotes", "Quotes", "A program confirms each quote appears in its source file."),
    ],
}


# ---------------------------------------------------------------- primitives

def _f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def T(x, y, s, cls="art-lab", size=12, anchor="start", extra=""):
    """Text. `s` is markup (may hold <tspan>); escape plain user text first."""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text class="{cls}" x="{_f(x)}" y="{_f(y)}" font-size="{_f(size)}"{a}{extra}>{s}</text>'


def R(x, y, w, h, cls, rx=0, extra=""):
    r = f' rx="{_f(rx)}"' if rx else ""
    return f'<rect class="{cls}" x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}"{r}{extra}/>'


def P(d, cls="art-line", extra=""):
    if "art-draw" in cls.split() and "pathLength" not in extra:
        extra += ' pathLength="1"'
    return f'<path class="{cls}" d="{d}"{extra}/>'


def C(x, y, r, cls):
    return f'<circle class="{cls}" cx="{_f(x)}" cy="{_f(y)}" r="{_f(r)}"/>'


def G(body, cls="", extra=""):
    c = f' class="{cls}"' if cls else ""
    return f"<g{c}{extra}>{body}</g>"


def L(x1, y1, x2, y2, cls="art-line"):
    return P(f"M{_f(x1)} {_f(y1)}L{_f(x2)} {_f(y2)}", cls)


def bar(x, y, w, cls="art-bar", h=3.2):
    """A line of text drawn as a rounded bar."""
    return R(x, y - h / 2, w, h, cls, rx=h / 2)


def tick(x, y, s=1.0, cls="art-line"):
    return P(f"M{_f(x - 4 * s)} {_f(y)}l{_f(3 * s)} {_f(3 * s)} {_f(6 * s)}-{_f(7 * s)}", cls)


def cross(x, y, s=3.5, cls="art-line"):
    return P(f"M{_f(x - s)} {_f(y - s)}l{_f(2 * s)} {_f(2 * s)}m0-{_f(2 * s)}l-{_f(2 * s)} {_f(2 * s)}", cls)


def chip(x, y, w, label, solid=True, size=11.5, cls_extra="", h=17):
    """A small tag. Solid = ink fill with paper text; else ink outline."""
    if solid:
        body = R(x, y, w, h, "art-fill", rx=h / 2) + T(x + w / 2, y + h / 2 + size * 0.35, label, "art-chipt", size, "middle")
    else:
        body = R(x, y, w, h, "art-chipline", rx=h / 2) + T(x + w / 2, y + h / 2 + size * 0.35, label, "art-labi", size, "middle")
    return G(body, cls_extra)


def frac(cx, ybar, num, den, size=16, w=None, cls="art-f"):
    w = w or max(len(den), len(num)) * size * 0.46 + 6
    return (T(cx, ybar - size * 0.3, num, cls, size, "middle")
            + L(cx - w / 2, ybar, cx + w / 2, ybar, "art-rule")
            + T(cx, ybar + size * 0.92, den, cls, size, "middle"))


def _cubic(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def _smooth(pts):
    """Catmull-Rom through points, as cubic Beziers."""
    d = [f"M{_f(pts[0][0])} {_f(pts[0][1])}"]
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{_f(c1[0])} {_f(c1[1])} {_f(c2[0])} {_f(c2[1])} {_f(p2[0])} {_f(p2[1])}")
    return "".join(d)


def plait(p0, p3, c1=None, c2=None, amp=2.6, crossings=3, cls="", ends=True, delay=""):
    """The house thread: two strands braided along a cubic from p0 to p3."""
    if c1 is None:
        c1 = (p0[0] + (p3[0] - p0[0]) * 0.5, p0[1])
    if c2 is None:
        c2 = (p0[0] + (p3[0] - p0[0]) * 0.5, p3[1])
    n = 36
    base = [_cubic(p0, c1, c2, p3, i / n) for i in range(n + 1)]
    a, b = [], []
    for i, (x, y) in enumerate(base):
        j0, j1 = max(i - 1, 0), min(i + 1, n)
        dx, dy = base[j1][0] - base[j0][0], base[j1][1] - base[j0][1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        s = amp * math.sin(math.pi * (crossings + 1) * i / n)
        a.append((x + nx * s, y + ny * s))
        b.append((x - nx * s, y - ny * s))
    d = f' class="art-draw {delay}" pathLength="1"' if delay else ' class="art-draw" pathLength="1"'
    body = (f'<path{d.replace("art-draw", "art-strand art-strand-b art-draw")} d="{_smooth(b)}"/>'
            f'<path{d.replace("art-draw", "art-strand art-strand-a art-draw")} d="{_smooth(a)}"/>')
    if ends:
        body += C(p0[0], p0[1], 2.6, "art-fill") + C(p3[0], p3[1], 2.6, "art-fill")
    return G(body, ("art-thread " + cls).strip())


def spin(x, y, up, h=7.0, flip=False, cls="art-spin"):
    """A ±1 spin as an arrow. flip=True animates from the opposite direction."""
    d = (f"M{_f(x)} {_f(y + h)}V{_f(y - h)}M{_f(x - 3.4)} {_f(y - h + 3.6)}"
         f"L{_f(x)} {_f(y - h)}L{_f(x + 3.4)} {_f(y - h + 3.6)}")
    inner = P(d, cls + (" art-flip" if flip else ""))
    if up:
        return inner
    return f'<g transform="rotate(180 {_f(x)} {_f(y)})">{inner}</g>'


def hatch(kind):
    return (f'<defs><pattern id="art-hatch-{kind}" width="5" height="5" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate(45)"><path class="art-hatchline" d="M0 0V5"/></pattern></defs>')


def hatch_fill(kind):
    return f' fill="url(#art-hatch-{kind})"'


def halo(x, y, w, h, states, rx=4):
    cls = "art-halo " + " ".join(f"art-hl-{s}" for s in states.split())
    return R(x, y, w, h, cls, rx=rx)


def dim(body, states):
    return G(body, " ".join(f"art-dim-{s}" for s in states.split()))


def page(x, y, w, h, lines, cls="art-frame", start=None, gap=10, seed=1, inset=10):
    rnd = random.Random(seed)
    out = [R(x, y, w, h, cls, rx=3)]
    yy = start if start is not None else y + 14
    for i in range(lines):
        ww = (w - 2 * inset) * (0.55 + 0.45 * rnd.random()) if i % 4 != 3 else (w - 2 * inset) * 0.42
        out.append(bar(x + inset, yy, ww))
        yy += gap
    return "".join(out)


def svg(kind, body, box):
    w, h = box
    tier = "art-door" if kind in DOOR_KINDS else "art-p"
    return (f'<svg class="specimen specimen--{_escape(kind)} art {tier}" viewBox="0 0 {w} {h}" '
            f'fill="none" aria-hidden="true" focusable="false">{body}</svg>')


# ------------------------------------------------------------- shared parts

def sum257(x, y, big=30, size=16):
    """Σ_{n∈A} 1/(2ⁿ − 1), with the limit set under the sigma."""
    return (T(x, y, "Σ", "art-f", big)
            + T(x + big * 0.33, y + size * 0.95, "n∈A", "art-fi", size * 0.75, "middle")
            + frac(x + big * 0.68 + 27, y - big * 0.34, "1", "2ⁿ − 1", size, w=50))


def loglog(ox, oy, w, h, kind, labels=True, small=False, pts=True, state_cls=""):
    """R(f) against Q(f) on log scales: R = Q, the 2020 bound R = O(Q⁴) and the
    region above it ruled out, and OpenAI's family on R = Q^(4−o(1))."""
    x1, ytop = ox + w, oy - h
    q4 = lambda x: oy - (x - ox) * h / w           # slope 4 in log units
    q1 = lambda x: oy - (x - ox) * h / w / 4        # slope 1
    out = []
    out.append(P(f"M{_f(ox)} {_f(oy)}L{_f(x1)} {_f(q4(x1))}L{_f(x1)} {_f(ytop)}L{_f(ox)} {_f(ytop)}Z",
                 "art-hatchfill " + state_cls.get("hatch", ""), hatch_fill(kind)))
    out.append(L(ox, oy, x1, oy, "art-axis"))
    out.append(L(ox, oy, ox, ytop, "art-axis"))
    out.append(P(f"M{_f(x1 - 4)} {_f(oy - 3)}L{_f(x1)} {_f(oy)}L{_f(x1 - 4)} {_f(oy + 3)}", "art-axis"))
    out.append(P(f"M{_f(ox - 3)} {_f(ytop + 4)}L{_f(ox)} {_f(ytop)}L{_f(ox + 3)} {_f(ytop + 4)}", "art-axis"))
    out.append(L(ox, oy, x1, q1(x1), "art-line-q art-dashed"))
    out.append(G(L(ox, oy, x1, q4(x1), "art-line art-draw"), state_cls.get("bound", "")))
    if pts:
        dots = []
        xs = [ox + w * f for f in ((0.22, 0.4, 0.58, 0.76, 0.94) if not small else (0.3, 0.55, 0.8))]
        curve = []
        for i in range(0, 41):
            u = 4 * i / 40
            eps = 1.5 / (1 + u)
            x = ox + w * u / 4
            curve.append((x, oy - (h / 4) * u * (4 - eps) / 4 * 1.0))
        for x in xs:
            u = 4 * (x - ox) / w
            eps = 1.5 / (1 + u)
            y = oy - (h / 4) * u * (4 - eps) / 4
            dots.append(C(x, y, 3 if not small else 2.6, "art-fill art-pop"))
        out.append(G(P(_smooth(curve[2:]), "art-line art-thin art-draw art-d2", ' pathLength="1"') + "".join(dots),
                     state_cls.get("sep", "")))
    return "".join(out)


def spin_grid(x0, y0, cell, bits, diff=(), flip=False, h=6.0):
    out = []
    for i, b in enumerate(bits):
        r, c = divmod(i, 4)
        cx, cy = x0 + c * cell + cell / 2, y0 + r * cell + cell / 2
        if i in diff:
            out.append(R(cx - cell / 2 + 1.2, cy - cell / 2 + 1.2, cell - 2.4, cell - 2.4, "art-tint", rx=3))
        out.append(spin(cx, cy, b, h=h, flip=flip and i in diff,
                        cls="art-spin art-spin-ink" if i in diff else "art-spin"))
    return "".join(out)


SIGMA = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0]
DIFF = (0, 3, 5, 6, 9, 10, 12, 15)          # 8 of 16 flipped
TAU = [(1 - b) if i in DIFF else b for i, b in enumerate(SIGMA)]


def run_strip(x, y, n, cell=12, gap=4.4, cls_on="art-fill", delay_base=0):
    out = []
    for i in range(10):
        on = i < n
        out.append(R(x + i * (cell + gap), y, cell, cell, (cls_on if on else "art-cell") + (" art-pop" if on else ""), rx=2))
    return "".join(out)


def pile(x, base, w, pages, scale, ink=False, every=8):
    """A stack of paper drawn to scale: height = pages × scale; one line per `every` pages."""
    h = pages * scale
    out = [R(x, base - h, w, h, "art-pile" + (" art-pile-ink" if ink else ""), rx=1.5)]
    k = every
    while k < pages:
        yy = base - k * scale
        out.append(L(x + 1.5, yy, x + w - 1.5, yy, "art-pageline"))
        k += every
    return "".join(out)


def filmframe(x, y, w, h, arrows=True, cue=False):
    out = [R(x, y, w, h, "art-frame-ink", rx=3)]
    if arrows:
        ax = [x + w * f for f in (0.25, 0.5, 0.75)]
        for i, cx in enumerate(ax):
            on = i == 2
            cls = "art-line art-cuearrow" if on else "art-line-q"
            out.append(P(f"M{_f(cx - 8)} {_f(y + h * 0.48)}h14m-4.5 -4.5 4.5 4.5-4.5 4.5", cls))
        out.append(L(x + 8, y + h - 8, x + w - 8, y + h - 8, "art-hair"))
        out.append(C(x + w * 0.72, y + h - 8, 2.4, "art-fill"))
    return "".join(out)


def waveform(x0, x1, yc, amp, seed=4, step=3.0, cls="art-wave"):
    rnd = random.Random(seed)
    d = []
    x = x0
    i = 0
    while x <= x1:
        env = 0.35 + 0.65 * abs(math.sin(i * 0.23)) * (0.6 + 0.4 * rnd.random())
        a = amp * env
        d.append(f"M{_f(x)} {_f(yc - a)}V{_f(yc + a)}")
        x += step
        i += 1
    return P("".join(d), cls)


# --------------------------------------------------------------------- doors

def _door_research():
    k = "research"
    o = [hatch(k)]
    # 1. Erdős #257: the series itself and its first terms.
    o.append(sum257(10, 66, big=32, size=17))
    o.append(T(62, 108, "1, 1/3, 1/7, 1/15, …", "art-fq", 12.5, "middle"))
    o.append(T(62, 146, "Erdős #257", "art-lab", 12, "middle"))
    # 2. Quantum queries: R(f) against Q(f), log scales.
    o.append(loglog(146, 116, 92, 92, k, small=True, state_cls={}))
    o.append(T(140, 24, "R", "art-fi", 13, "end"))
    o.append(T(244, 130, "Q", "art-fi", 13))
    o.append(R(150, 30, 42, 18, "art-paperf", rx=2))
    o.append(T(153, 43, "O(Q⁴)", "art-f", 13))
    o.append(T(192, 146, "quantum queries", "art-lab", 12, "middle"))
    # 3. Spin glass: two near-best arrangements, half the spins differ.
    o.append(T(290, 22, "σ", "art-fi", 15, "middle"))
    o.append(T(350, 22, "τ", "art-fi", 15, "middle"))
    o.append(spin_grid(266, 32, 12, SIGMA, h=4.6))
    o.append(spin_grid(326, 32, 12, TAU, diff=DIFF, flip=True, h=4.6))
    o.append(T(320, 102, "8 of 16 differ", "art-labi", 12, "middle"))
    o.append(T(320, 146, "spin glass", "art-lab", 12, "middle"))
    # The thread: all three are Lean-checked.
    o.append(plait((14, 164), (322, 164), amp=2.4, crossings=7, ends=False))
    for x in (62, 192):
        o.append(C(x, 164, 3, "art-fill"))
    o.append(chip(324, 155, 50, "Lean ✓", size=12, h=18))
    return svg(k, "".join(o), (380, 180))


def _door_proofs():
    k = "proofs"
    o = []
    # The paper, one sentence highlighted.
    o.append(R(8, 8, 128, 140, "art-frame", rx=3))
    o.append(bar(20, 24, 74, "art-bar art-bar-strong", 4.2))
    rnd = random.Random(7)
    ys = [42, 53, 64, 75, 86, 97, 108, 119, 130]
    for i, y in enumerate(ys):
        if y in (75, 86):
            continue
        o.append(bar(20, y, 104 * (0.6 + 0.4 * rnd.random()) if i != 8 else 52))
    o.append(R(16, 69, 112, 23, "art-tint art-sentence", rx=3))
    o.append(bar(20, 75, 100, "art-fill"))
    o.append(bar(20, 86, 62, "art-fill"))
    o.append(T(72, 168, "a sentence in the paper", "art-lab", 12, "middle"))
    # The thread to the Lean that proves it.
    o.append(plait((128, 86), (204, 58), amp=2.6, crossings=3))
    # Lean statements, each labelled by how much of the sentence it covers.
    o.append(R(200, 14, 174, 134, "art-frame", rx=3))
    o.append(T(212, 34, "Lean 4", "art-lab", 12))
    rows = [(58, "exact", True), (90, "stronger", False), (122, "partial", False)]
    for i, (y, tag, solid) in enumerate(rows):
        o.append(G(T(212, y + 4, "theorem", "art-monoi", 12) + bar(268, y, 30 + 8 * (i % 2), "art-bar")
                   + chip(306, y - 9, 58, tag, solid=solid, size=11.5, h=18,
                          cls_extra=("art-dashchip" if tag == "partial" else "")),
                   f"art-pop art-d{i + 1}"))
    o.append(T(287, 168, "the Lean, and what it covers", "art-lab", 12, "middle"))
    return svg(k, "".join(o), (380, 180))


def _door_assistants():
    k = "assistants"
    o = []
    # Agent Trace: each command with its saved status and exit code.
    o.append(R(6, 8, 190, 112, "art-frame", rx=4))
    o.append(T(16, 26, "session transcript", "art-lab", 11.5))
    rows = [
        (50, "test", "exit 1", False),
        (76, "edit", "1 line", None),
        (102, "test", "exit 0", True),
    ]
    for i, (y, cmd, st, ok) in enumerate(rows):
        g = T(16, y, "$", "art-monoq", 12) + T(28, y, cmd, "art-mono", 12)
        if ok is None:
            g += T(118, y, "−1 +1", "art-monoi", 12, "end")
            g += T(186, y, st, "art-mono", 12, "end")
        else:
            g += (tick(128, y - 4, 0.9) if ok else cross(128, y - 4, 3.2))
            g += T(186, y, st, "art-mono" + (" art-inkt" if ok else ""), 12, "end")
        o.append(G(g, f"art-pop art-d{i + 1}"))
    # One Checkout: A's patch committed on HEAD; B's edits kept.
    o.append(L(24, 146, 84, 146, "art-line-q"))
    o.append(C(24, 146, 5.5, "art-node"))
    o.append(G(C(84, 146, 6.5, "art-fill"), "art-pop art-d2"))
    o.append(T(24, 172, "HEAD", "art-mono", 11.5, "middle"))
    o.append(T(84, 172, "+ patch", "art-monoi", 11.5, "middle"))
    o.append(R(112, 135, 84, 22, "art-frame art-dashrect", rx=3))
    o.append(T(154, 150, "B's edits kept", "art-lab", 11.5, "middle"))
    # Safety Core: made-up value committed, out of 10 runs.
    o.append(T(212, 22, "made-up value committed", "art-txt", 12))
    for j, (label, n) in enumerate((("no rule", 10), ("written rule", 6), ("hook", 0))):
        y = 44 + j * 40
        o.append(T(212, y, label, "art-lab", 12))
        o.append(T(374, y, f"{n} of 10", "art-labi" if n == 0 else "art-txt", 12, "end"))
        o.append(run_strip(212, y + 6, n))
    o.append(T(212, 172, "Claude Haiku 4.5", "art-lab", 11.5))
    return svg(k, "".join(o), (380, 180))


def _door_explaining():
    k = "explaining"
    o = []
    base, sc = 100, 0.42
    o.append(R(6, 46, 58, 54, "art-frame-ink", rx=3))
    o.append(T(35, 70, "#257", "art-f", 16, "middle"))
    o.append(T(35, 88, "Lean ✓", "art-labi", 11.5, "middle"))
    xs = [(88, 152, "152 pages"), (154, 26, "26 pages"), (220, 16, "16 pages")]
    for i, (x, n, lab) in enumerate(xs):
        o.append(plait((64, 73), (x + 2, base - n * sc - 3), c1=(76, 73), c2=(x - 8, base - n * sc - 3),
                       amp=1.6, crossings=2, ends=False, delay=f"art-d{i}"))
        o.append(G(pile(x, base, 52, n, sc), f"art-rise art-d{i + 1}"))
        o.append(T(x + 26, 120, lab, "art-txt", 12, "middle"))
    o.append(plait((64, 73), (288, 60), c1=(120, 30), c2=(240, 40), amp=1.6, crossings=4, ends=False, delay="art-d3"))
    o.append(filmframe(288, 44, 86, 56))
    o.append(T(331, 120, "video", "art-txt", 12, "middle"))
    # One spoken sentence: a recorded word times the third arrow.
    o.append(waveform(8, 372, 144, 7, seed=3))
    widths = [22, 34, 18, 40, 26, 30, 20, 38, 28, 36, 24]
    x = 8
    for i, w in enumerate(widths):
        cue = i == 9
        o.append(R(x, 160, w, 10, "art-fill art-cueword" if cue else "art-word", rx=2))
        if cue:
            cx = x + w / 2
        x += w + 5
    o.append(P(f"M{_f(cx)} 158V{_f(102)}", "art-line art-dashed art-draw art-d2", ' pathLength="1"'))
    o.append(T(cx - 22, 152, "cue word", "art-labi", 11.5, "end"))
    return svg(k, "".join(o), (380, 180))


def _codefile(x, y, w, h, name_w, defs, heads=2, seed=2, ink_def=None):
    rnd = random.Random(seed)
    o = [R(x, y, w, h, "art-frame", rx=4)]
    o.append(R(x + 8, y + 7, 12, 14, "art-filetab", rx=1.5))
    o.append(bar(x + 26, y + 14, name_w, "art-bar art-bar-strong", 4))
    yy = y + 34
    o.append(T(x + 10, yy + 4, '"""', "art-monoi", 12))
    for hh in range(heads):
        o.append(bar(x + 32, yy, 22, "art-fill", 3.4))
        o.append(bar(x + 58, yy, (w - 70) * (0.5 + 0.4 * rnd.random())))
        yy += 11
    rows = []
    for j in range(defs):
        yy += 4
        o.append(T(x + 10, yy + 4, "def", "art-monoi" if ink_def == j else "art-mono", 12))
        o.append(bar(x + 38, yy, 34 + 10 * rnd.random(), "art-fill" if ink_def == j else "art-bar art-bar-strong", 3.6))
        rows.append(yy)
        yy += 13
    return "".join(o), rows


def _door_code():
    k = "code"
    o = []
    a, ra = _codefile(6, 6, 140, 82, 46, 2, seed=3, ink_def=0)
    b, rb = _codefile(6, 98, 140, 76, 38, 1, seed=5)
    o += [a, b]
    # B's function calls A's first function: the CodeMap link.
    o.append(T(100, rb[0] + 4, "f()", "art-monoi", 12))
    o.append(plait((119, rb[0]), (88, ra[0]), c1=(162, rb[0]), c2=(162, ra[0]), amp=2, crossings=3))
    o.append(T(150, 96, "calls", "art-labi", 11.5))
    # DuckDB: functions and calls written by static analysis.
    cx, top = 226, 22
    o.append(P(f"M{cx - 26} {top}v58a26 8 0 0 0 52 0v-58", "art-frame-ink"))
    o.append(P(f"M{cx - 26} {top}a26 8 0 0 0 52 0a26 8 0 0 0 -52 0Z", "art-frame-ink"))
    o.append(P(f"M{cx - 26} {top + 29}a26 8 0 0 0 52 0", "art-line art-thin"))
    o.append(T(cx, 112, "DuckDB", "art-txt", 12, "middle"))
    o.append(plait((146, 46), (cx - 30, 52), amp=1.8, crossings=2, ends=False))
    for i, (tx, lab) in enumerate(((266, "functions"), (322, "calls"))):
        tw = 52
        o.append(R(tx, 22, tw, 64, "art-frame", rx=3))
        o.append(R(tx, 22, tw, 16, "art-tint", rx=3))
        o.append(T(tx + tw / 2, 34, lab, "art-labi", 11, "middle"))
        for r in range(4):
            yy = 48 + r * 10
            if lab == "calls":
                o.append(bar(tx + 6, yy, 16) + P(f"M{tx + 25} {yy}h4", "art-line-q") + bar(tx + 32, yy, 14))
            else:
                o.append(bar(tx + 6, yy, 24 + 10 * (r % 2)))
    # A recursive query over calls: every caller of f.
    o.append(R(194, 126, 180, 48, "art-frame-ink", rx=4))
    o.append(T(204, 146, "WITH RECURSIVE", "art-monoi", 12))
    o.append(T(204, 164, "callers of f(…)", "art-mono", 12))
    return svg(k, "".join(o), (380, 180))


def _door_testing():
    k = "testing"
    o = [hatch(k)]
    # 28 practice problems; their missed bugs go back to the model.
    o.append(T(8, 24, "28 practice", "art-lab", 12))
    for i in range(28):
        r, c = divmod(i, 7)
        o.append(R(8 + c * 13, 36 + r * 13, 10, 10, "art-cell", rx=1.5))
    o.append(T(8, 108, "missed bugs", "art-labi", 12))
    o.append(T(8, 122, "shown to the model", "art-lab", 12))
    o.append(plait((102, 62), (164, 104), c1=(140, 62), c2=(130, 104), amp=2, crossings=3))
    # 58 held-out problems: share of bugs caught.
    o.append(T(168, 24, "bugs caught, 58 held-out problems", "art-lab", 12))
    x0, W = 168, 206
    o.append(R(x0, 40, W, 6, "art-track", rx=1))
    for v in (0, 50, 100):
        o.append(L(x0 + W * v / 100, 36, x0 + W * v / 100, 50, "art-hair"))
    o.append(T(x0, 62, "0", "art-lab", 11, "middle"))
    o.append(T(x0 + W / 2, 62, "50", "art-lab", 11, "middle"))
    o.append(T(x0 + W, 62, "100%", "art-lab", 11, "end"))
    w69, w77 = W * 0.69, W * 0.77
    o.append(R(x0, 76, w69, 18, "art-barq art-grow", rx=2))
    o.append(T(x0 + w69 + 8, 90, "69%", "art-f", 16))
    o.append(G(R(x0, 102, w69, 22, "art-fill", rx=2)
               + R(x0 + w69, 102, (w77 - w69) / 2, 22, "art-fill")
               + R(x0 + w69 + (w77 - w69) / 2, 102, (w77 - w69) / 2, 22, "art-hatchbar", rx=0, extra=hatch_fill(k))
               + R(x0 + w69 + (w77 - w69) / 2, 102, (w77 - w69) / 2, 22, "art-chipline"),
               "art-grow art-d1"))
    o.append(T(x0 + w77 + 8, 120, "77%", "art-fink", 22))
    o.append(T(x0, 146, "before", "art-lab", 11.5))
    o.append(L(x0 + w69 + (w77 - w69) * 0.75, 126, x0 + w69 + (w77 - w69) * 0.75, 136, "art-line art-thin"))
    o.append(T(x0 + w69 + (w77 - w69) * 0.75, 150, "≈ half the rise: timeouts", "art-labi", 11.5, "end"))
    o.append(T(x0, 172, "DeepSeek V4.1 Flash", "art-lab", 11.5))
    return svg(k, "".join(o), (380, 180))


# ------------------------------------------------------------------ projects

def _p_maths():
    k = "maths"
    o = []
    # The map: eight Erdős problems, #257 the worked case.
    nodes = [(30, 52), (74, 40), (52, 80), (94, 82), (22, 112), (66, 124), (36, 160), (86, 156)]
    edges = [(0, 1), (0, 2), (1, 3), (2, 3), (2, 4), (2, 5), (4, 6), (5, 6), (5, 7), (3, 7)]
    m = [L(*nodes[a], *nodes[b], "art-hair") for a, b in edges]
    for i, (x, y) in enumerate(nodes):
        m.append(C(x, y, 5, "art-node") if i != 5 else "")
    m.append(T(14, 22, "8 Erdős problems", "art-lab", 12))
    o.append(G("".join(m), "art-dim-proved art-dim-open"))
    o.append(C(66, 124, 8.5, "art-fill"))
    o.append(T(80, 143, "#257", "art-labi", 12.5))
    o.append(plait((74, 124), (128, 66), c1=(104, 124), c2=(98, 66), amp=2.2, crossings=3, ends=False))
    # The question: the series and its terms.
    q = [halo(126, 22, 268, 86, "question")]
    q.append(sum257(132, 74, big=34, size=17))
    q.append(T(254, 44, "n", "art-fi", 13, "end"))
    for i, (n, v) in enumerate(((1, "1"), (2, "1/3"), (3, "1/7"), (4, "1/15"))):
        cx = 272 + i * 30
        q.append(T(cx, 44, str(n), "art-f", 13, "middle"))
        q.append(T(cx, 70, v, "art-f", 13.5, "middle"))
    q.append(L(244, 52, 392, 52, "art-hair"))
    q.append(T(384, 44, "…", "art-f", 13, "middle"))
    q.append(T(384, 70, "…", "art-f", 13, "middle"))
    q.append(T(392, 98, "irrational for every infinite A?", "art-labi", 12, "end"))
    o.append(G("".join(q)))
    # The answer so far.
    a = [halo(122, 116, 274, 46, "proved", rx=6)]
    a.append(R(126, 120, 266, 38, "art-frame-ink", rx=4))
    a.append(T(136, 144, "if  Σ<tspan dy='4' font-size='11'>n∈A</tspan><tspan dy='-4'> 1/n &lt; ∞</tspan>", "art-f", 15))
    a.append(T(255, 144, "⇒  irrational", "art-f", 15))
    a.append(chip(340, 130, 44, "Lean ✓", size=11.5, h=18))
    o.append(G("".join(a), "art-dim-open"))
    b = [halo(122, 166, 274, 46, "open", rx=6)]
    b.append(R(126, 170, 266, 38, "art-frame art-dashrect", rx=4))
    b.append(T(136, 194, "every infinite A", "art-txt", 13))
    b.append(chip(340, 180, 44, "open", solid=False, size=11.5, h=18, cls_extra="art-dashchip"))
    o.append(G("".join(b), "art-dim-proved"))
    return svg(k, "".join(o), (400, 220))


def _p_quartic():
    k = "quartic"
    o = [hatch(k)]
    ox, oy, w, h = 42, 186, 196, 160
    o.append(loglog(ox, oy, w, h, k, state_cls={
        "hatch": "art-dim-separation art-dim-query",
        "bound": "",
        "sep": "art-dim-bound art-dim-query"}))
    o.append(T(ox - 6, oy - h + 6, "R(f)", "art-fi", 13, "end"))
    o.append(T(ox + w, oy + 18, "Q(f)", "art-fi", 13, "end"))
    o.append(T(ox + 4, oy + 18, "log scales", "art-lab", 11))
    o.append(G(halo(ox + 6, oy - h + 6, 112, 24, "bound")
               + R(ox + 10, oy - h + 10, 104, 18, "art-paperf", rx=2)
               + T(ox + 14, oy - h + 23, "2020: R = O(Q⁴)", "art-f", 13), "art-dim-separation art-dim-query"))
    o.append(T(ox + w - 2, oy - h / 4 - 8, "R = Q", "art-fq", 12.5, "end"))
    o.append(G(halo(ox + 88, oy - 74, 112, 26, "separation")
               + T(ox + 94, oy - 56, "R = Q<tspan dy='-6' font-size='10.5'>4−o(1)</tspan>", "art-fink", 13.5),
               "art-dim-bound art-dim-query"))
    # The Lean proof and Comparator's verdicts.
    x = 256
    lean = [R(x, 14, 138, 104, "art-frame", rx=4)]
    lean.append(T(x + 10, 32, "Lean 4, AI-written", "art-lab", 11.5))
    lean.append(T(x + 10, 54, "≈ 29,000 lines", "art-f", 16))
    lean.append(T(x + 10, 76, "Comparator", "art-lab", 11.5))
    lean.append(tick(x + 15, 89, 0.95))
    lean.append(T(x + 26, 93, "main theorem", "art-txt", 12))
    for i in range(5):
        lean.append(cross(x + 15 + i * 12, 106, 3.2))
    lean.append(T(x + 76, 110, "5 broken", "art-txt", 12))
    o.append(G("".join(lean), "art-dim-query"))
    # One query: one look at one input bit.
    q = [halo(x - 4, 128, 146, 86, "query", rx=6)]
    q.append(T(x + 2, 146, "1 query = 1 bit read", "art-labi", 12))
    bits = "01101001"
    for i, bch in enumerate(bits):
        bx = x + 2 + i * 17
        q.append(R(bx, 158, 15, 20, "art-frame-ink" if i == 5 else "art-frame", rx=2))
        q.append(T(bx + 7.5, 172.5, bch, "art-mono" if i != 5 else "art-monoi", 12.5, "middle"))
    q.append(P(f"M{x + 2 + 5 * 17 + 7.5} 182v14m-4 -10 4-4 4 4", "art-line"))
    q.append(T(x + 2, 206, "x₁ … x₈", "art-fi", 12.5))
    o.append(G("".join(q), "art-dim-bound art-dim-separation"))
    return svg(k, "".join(o), (400, 220))


def _p_lean_exposition():
    k = "lean-exposition"
    o = []
    # Four spins, six couplings.
    pts = [(30, 54), (100, 54), (30, 116), (100, 116)]
    up = [1, 0, 0, 1]
    c = [halo(8, 18, 116, 120, "couplings", rx=8)]
    for i in range(4):
        for j in range(i + 1, 4):
            c.append(L(*pts[i], *pts[j], "art-coupling"))
    for i, (x, y) in enumerate(pts):
        c.append(C(x, y, 12, "art-paperf art-node"))
        c.append(spin(x, y, up[i], h=6.5, cls="art-spin art-spin-ink"))
    c.append(T(65, 78, "J", "art-fi", 13, "middle"))
    c.append(T(65, 32, "4 spins, 6 couplings", "art-lab", 11.5, "middle"))
    o.append(G("".join(c), "art-dim-count"))
    # All 2⁴ = 16 arrangements of the four spins, each a 2×2 of ±1.
    s = [halo(6, 140, 120, 76, "count", rx=8)]
    s.append(T(66, 156, "2⁴ = 16 arrangements", "art-lab", 11.5, "middle"))
    for n in range(16):
        r, cc = divmod(n, 8)
        gx, gy = 10 + cc * 14.5, 166 + r * 22
        for b in range(4):
            on = (n >> (3 - b)) & 1
            bx, by = gx + (b % 2) * 5.5, gy + (b // 2) * 5.5
            s.append(R(bx, by, 4.5, 4.5, "art-fill" if on else "art-cell", rx=0.8))
    o.append(G("".join(s), "art-dim-couplings"))
    # Large N: two near-best arrangements differing in about half their spins.
    g = [halo(144, 14, 254, 200, "overlap", rx=8)]
    cell = 22
    g.append(T(150 + 44, 34, "σ", "art-fi", 17, "middle"))
    g.append(T(300 + 44, 34, "τ", "art-fi", 17, "middle"))
    g.append(R(150, 44, 88, 88, "art-frame", rx=3))
    g.append(R(300, 44, 88, 88, "art-frame", rx=3))
    g.append(spin_grid(150, 44, cell, SIGMA, diff=DIFF, h=7))
    g.append(spin_grid(300, 44, cell, TAU, diff=DIFF, flip=True, h=7))
    g.append(T(269, 84, "≠", "art-fink", 20, "middle"))
    g.append(plait((242, 98), (296, 98), amp=2, crossings=3, ends=False))
    g.append(T(269, 156, "near-best arrangements", "art-lab", 12, "middle"))
    g.append(T(269, 178, "8 of 16 spins differ", "art-labi", 12.5, "middle"))
    g.append(T(269, 200, "large N: about half differ", "art-txt", 12.5, "middle"))
    o.append(G("".join(g), "art-dim-couplings art-dim-count"))
    return svg(k, "".join(o), (400, 220))


def _p_proof_reader():
    k = "proof-reader"
    o = []
    # The paper with one sentence selected.
    pg = [R(8, 10, 148, 202, "art-frame", rx=3)]
    pg.append(T(18, 30, "Contextual", "art-ft", 13.5))
    pg.append(T(18, 46, "Embeddings", "art-ft", 13.5))
    pg.append(T(18, 62, "PLDI 2026", "art-lab", 11))
    rnd = random.Random(11)
    for i, y in enumerate(range(75, 206, 11)):
        if y in (108, 119):
            continue
        pg.append(bar(18, y, 128 * (0.55 + 0.45 * rnd.random()) if i % 5 != 4 else 60))
    pg.append(R(14, 102, 138, 23, "art-tint", rx=3))
    pg.append(bar(18, 108, 126, "art-fill"))
    pg.append(bar(18, 119, 76, "art-fill"))
    o.append(G("".join(pg)))
    o.append(plait((150, 119), (196, 50), c1=(176, 119), c2=(170, 50), amp=2.4, crossings=3))
    # Five lines of the authors' Lean proof.
    ln = [halo(190, 8, 206, 98, "sentence", rx=6)]
    ln.append(R(194, 12, 198, 90, "art-frame-ink", rx=4))
    ln.append(T(204, 30, "authors' Lean, 5 lines", "art-lab", 11.5))
    widths = [(0, 120), (10, 96), (10, 132), (20, 84), (10, 104)]
    for i, (ind, w) in enumerate(widths):
        y = 44 + i * 12
        ln.append(T(210, y + 4, str(i + 1), "art-monoq", 11, "end"))
        ln.append(bar(218 + ind, y, w * 0.95, "art-fill" if i == 0 else "art-bar art-bar-ink"))
    o.append(G("".join(ln), "art-dim-graph art-dim-axioms"))
    # Dependency graph.
    dg = [halo(190, 112, 112, 102, "graph", rx=6)]
    dg.append(T(196, 128, "dependencies", "art-lab", 11.5))
    nodes = [(246, 144), (216, 172), (276, 172), (232, 200), (290, 200)]
    for a, b in ((0, 1), (0, 2), (1, 3), (2, 3), (2, 4)):
        dg.append(L(*nodes[a], *nodes[b], "art-line-q"))
    for i, (x, y) in enumerate(nodes):
        dg.append(C(x, y, 6, "art-fill" if i == 0 else "art-node"))
    o.append(G("".join(dg), "art-dim-sentence art-dim-axioms"))
    # Axioms, as Lean reports them.
    ax = [halo(306, 112, 90, 102, "axioms", rx=6)]
    ax.append(R(310, 116, 82, 94, "art-frame", rx=4))
    ax.append(T(318, 134, "axioms", "art-lab", 11.5))
    for i in range(3):
        y = 152 + i * 16
        ax.append(C(322, y, 2.4, "art-fill"))
        ax.append(bar(330, y, 40 + 10 * (i % 2), "art-bar art-bar-strong"))
    o.append(G("".join(ax), "art-dim-sentence art-dim-graph"))
    return svg(k, "".join(o), (400, 220))


def _p_atlas():
    k = "atlas"
    o = []
    rnd = random.Random(372)
    centres = [(52, 70, 22), (118, 52, 18), (182, 78, 24), (70, 140, 20), (142, 132, 26),
               (214, 150, 18), (40, 190, 14), (112, 194, 16), (200, 204, 12)]
    dots = []
    counts = [52, 36, 58, 40, 64, 34, 30, 34, 24]   # 372 families in all
    pi_dot = None
    for (cx, cy, sp), n in zip(centres, counts):
        for _ in range(n):
            a, r = rnd.random() * math.tau, sp * math.sqrt(rnd.random())
            x, y = cx + r * math.cos(a) * 1.3, cy + r * math.sin(a) * 0.85
            dots.append(C(x, y, 1.9, "art-dot"))
            if pi_dot is None and cx == 142 and r > sp * 0.5 and math.cos(a) > 0.5:
                pi_dot = (x, y)
    m = [T(10, 22, "719 papers, 372 families", "art-lab", 12)] + dots
    o.append(G("".join(m), "art-dim-paper art-dim-verdicts"))
    px, py = pi_dot
    o.append(G(halo(px - 12, py - 12, 24, 24, "paper", rx=12) + C(px, py, 5, "art-fill art-pop")))
    o.append(plait((px + 6, py), (262, 48), c1=(px + 50, py), c2=(222, 48), amp=2.2, crossings=3, ends=False))
    # The paper about π and two checkers' verdicts on its Lean statement.
    card = [R(262, 14, 132, 196, "art-frame-ink", rx=4)]
    card.append(T(274, 56, "π", "art-fink", 30))
    card.append(T(300, 40, "one paper", "art-lab", 11.5))
    card.append(T(300, 56, "about π", "art-txt", 12.5))
    card.append(T(274, 82, "Lean statement", "art-lab", 11.5))
    card.append(R(274, 88, 108, 16, "art-tint", rx=2))
    card.append(T(280, 100, "theorem …", "art-monoi", 11.5))
    o.append(G("".join(card), "art-dim-map"))
    v = [halo(266, 112, 124, 94, "verdicts", rx=6)]
    v.append(T(274, 130, "MathVet", "art-txt", 12))
    v.append(R(274, 136, 108, 8, "art-fill", rx=1.5))
    v.append(T(382, 156, "full coverage", "art-labi", 11.5, "end"))
    v.append(T(274, 178, "cert-machine", "art-txt", 12))
    v.append(R(274, 184, 108, 8, "art-track", rx=1.5))
    v.append(R(274, 184, 62, 8, "art-fill", rx=1.5))
    v.append(T(382, 204, "narrower", "art-labi", 11.5, "end"))
    o.append(G("".join(v), "art-dim-map art-dim-paper"))
    return svg(k, "".join(o), (400, 220))


def _p_formal_verification():
    k = "formal-verification"
    o = []
    cx, cy, r = 106, 112, 72
    comp = []
    dafny_at = [3, 10, 17, 22, 30, 37, 45, 51, 58, 66, 73, 81]   # 12 calculations inside components
    for i in range(88):
        a = -math.pi / 2 + math.tau * i / 88
        comp.append(C(cx + r * math.cos(a), cy + r * math.sin(a), 2.1, "art-dot-strong"))
    o.append(G(halo(cx - r - 8, cy - r - 8, 2 * r + 16, 2 * r + 16, "components", rx=r + 8)
               + "".join(comp), "art-dim-coverage"))
    d = [halo(cx - 60, cy - 60, 120, 120, "dafny", rx=60)]
    for i in dafny_at:
        a = -math.pi / 2 + math.tau * i / 88
        x, y = cx + (r - 13) * math.cos(a), cy + (r - 13) * math.sin(a)
        d.append(P(f"M{_f(x)} {_f(y - 4.2)}l4.2 4.2-4.2 4.2-4.2-4.2Z", "art-fill"))
        d.append(L(x + 4.4 * math.cos(a), y + 4.4 * math.sin(a), cx + (r - 3) * math.cos(a), cy + (r - 3) * math.sin(a), "art-line art-thin"))
    for j in range(4):
        sx, sy = cx - 11 + (j % 2) * 14, cy - 11 + (j // 2) * 14
        d.append(R(sx, sy, 8, 8, "art-fill", rx=1.2))
    o.append(G("".join(d), "art-dim-coverage"))
    o.append(G(halo(cx - r - 21, cy - r - 21, 2 * r + 42, 2 * r + 42, "coverage", rx=r + 21)
               + C(cx, cy, r + 13, "art-ring-unknown"), "art-dim-dafny"))
    # Legend, in the order the rings read.
    x = 214
    rows = [
        (28, "88", "Python components", "dot", "art-dim-coverage"),
        (78, "16", "calculations proved in Dafny", "diamond", "art-dim-coverage"),
    ]
    for y, num, lab, glyph, dcls in rows:
        g = []
        if glyph == "dot":
            g.append(C(x + 5, y + 10, 3, "art-dot-strong"))
        else:
            g.append(P(f"M{x + 5} {y + 5.5}l4.5 4.5-4.5 4.5-4.5-4.5Z", "art-fill"))
        g.append(T(x + 18, y + 17, num, "art-f", 22))
        g.append(T(x + 48, y + 15, lab, "art-txt", 12))
        o.append(G("".join(g), dcls))
    o.append(G(T(x + 48, 112, "12 inside components", "art-lab", 11.5)
               + T(x + 48, 127, "4 shared", "art-lab", 11.5)
               + P(f"M{x + 48} 146h0", "art-line")
               + T(x + 48, 146, "compiled to Python", "art-labi", 11.5),
               "art-dim-coverage art-dim-components"))
    o.append(G(C(x + 7, 182, 7, "art-ring-unknown-s")
               + T(x + 22, 187, "unknown", "art-fi", 17)
               + T(x + 22, 204, "whole-claim coverage, all 88", "art-lab", 11.5),
               "art-dim-dafny art-dim-components"))
    return svg(k, "".join(o), (400, 220))


def _p_agent_trace():
    k = "agent-trace"
    o = []
    o.append(R(6, 8, 388, 206, "art-frame", rx=5))
    o.append(L(118, 8, 118, 214, "art-hair"))
    o.append(T(16, 30, "saved sessions", "art-lab", 11.5))
    for i, name in enumerate(("Claude Code", "Codex", "Claude Code")):
        y = 54 + i * 26
        if i == 0:
            o.append(R(10, y - 15, 104, 22, "art-wash", rx=3))
        o.append(C(19, y - 4, 2.6, "art-fill" if i == 0 else "art-dot-strong"))
        o.append(T(28, y, name, "art-txt" if i == 0 else "art-lab", 12))
    o.append(T(16, 196, "copy detail", "art-labi", 11.5))
    o.append(T(16, 208, "into another chat", "art-lab", 11))
    o.append(T(128, 30, "command", "art-lab", 11.5))
    o.append(T(384, 30, "status · exit", "art-lab", 11.5, "end"))
    # 1. Failing test.
    r1 = [halo(122, 38, 268, 52, "fail", rx=5)]
    r1.append(T(128, 58, "$ test", "art-mono", 12.5))
    r1.append(cross(312, 54, 3.4))
    r1.append(T(384, 58, "failed · 1", "art-monoi", 12.5, "end"))
    r1.append(R(128, 68, 256, 16, "art-wash", rx=2))
    r1.append(bar(134, 76, 120, "art-bar art-bar-strong"))
    o.append(G("".join(r1), "art-dim-fix art-dim-pass"))
    # 2. One-line fix.
    r2 = [halo(122, 96, 268, 52, "fix", rx=5)]
    r2.append(T(128, 116, "edit", "art-mono", 12.5))
    r2.append(T(384, 116, "1 line", "art-monoi", 12.5, "end"))
    r2.append(T(132, 138, "−", "art-mono", 13))
    r2.append(bar(146, 134, 150, "art-bar art-bar-strong"))
    r2.append(T(132, 138 + 0, "", "art-mono", 1))
    r2.append(R(128, 126, 256, 16, "art-wash", rx=2))
    r2.append(T(134, 138, "−", "art-mono", 13))
    r2.append(bar(146, 134, 150, "art-bar art-bar-strong"))
    r2.append(T(262, 138, "+", "art-monoi", 13))
    r2.append(bar(274, 134, 100, "art-fill"))
    o.append(G("".join(r2), "art-dim-fail art-dim-pass"))
    # 3. Passing rerun.
    r3 = [halo(122, 154, 268, 52, "pass", rx=5)]
    r3.append(T(128, 174, "$ test", "art-mono", 12.5))
    r3.append(tick(314, 170, 1))
    r3.append(T(384, 174, "passed · 0", "art-monoi", 12.5, "end"))
    r3.append(R(128, 184, 256, 16, "art-wash", rx=2))
    r3.append(bar(134, 192, 70, "art-bar art-bar-strong"))
    o.append(G("".join(r3), "art-dim-fail art-dim-fix"))
    return svg(k, "".join(o), (400, 220))


def _p_one_checkout():
    k = "one-checkout"
    o = []
    # Commit history: last commit, then the new commit carrying A's patch.
    o.append(T(14, 26, "commits", "art-lab", 11.5))
    o.append(L(40, 178, 40, 66, "art-line-q"))
    o.append(C(40, 178, 7, "art-node"))
    o.append(T(54, 182, "last commit", "art-txt", 12))
    o.append(T(54, 198, "HEAD before", "art-lab", 11))
    nc = [halo(24, 50, 104, 34, "result", rx=8)]
    nc.append(C(40, 66, 8.5, "art-fill"))
    nc.append(T(54, 64, "new commit", "art-txt", 12))
    nc.append(T(54, 79, "A's patch", "art-labi", 11.5))
    o.append(G("".join(nc), "art-hide-before art-dim-kept"))
    # Agent A's patch card.
    pa = [R(14, 104, 96, 50, "art-frame-ink", rx=4)]
    pa.append(T(22, 122, "agent A: patch", "art-labi", 11.5))
    pa.append(T(22, 140, "+", "art-monoi", 12.5))
    pa.append(bar(34, 136, 64, "art-fill"))
    o.append(G("".join(pa), "art-dim-kept"))
    o.append(G(plait((110, 128), (196, 92), c1=(150, 128), c2=(160, 92), amp=2.2, crossings=3, ends=False)
               + plait((48, 104), (44, 76), c1=(80, 92), c2=(70, 80), amp=1.6, crossings=1, ends=False),
               "art-dim-before art-dim-kept"))
    # The same file, line by line, with whose change each line carries.
    fx = 196
    f = [R(fx, 14, 198, 196, "art-frame", rx=4)]
    f.append(R(fx + 10, 22, 12, 14, "art-filetab", rx=1.5))
    f.append(T(fx + 28, 33, "the same file", "art-lab", 11.5))
    o.append(G("".join(f)))
    lines = ["", "", "A", "", "Bs", "Bs", "", "Bw", "", "", "Bw", ""]
    for i, who in enumerate(lines):
        y = 52 + i * 13.2
        w = 120 + (i * 37 % 50)
        if who == "A":
            o.append(G(halo(fx + 4, y - 7, 190, 14, "result", rx=3)
                       + T(fx + 12, y + 4, "A", "art-monoi", 11)
                       + bar(fx + 30, y, w, "art-fill"), "art-dim-kept"))
        elif who.startswith("B"):
            cls = "art-bline-staged" if who == "Bs" else "art-bline-work"
            o.append(G(halo(fx + 4, y - 7, 190, 14, "kept before", rx=3)
                       + T(fx + 12, y + 4, "B", "art-mono", 11)
                       + R(fx + 30, y - 2.2, w, 4.4, cls, rx=2.2), "art-dim-result"))
        else:
            o.append(bar(fx + 30, y, w))
    o.append(G(T(fx + 10, 204, "B: staged", "art-lab", 11)
               + R(fx + 70, 199, 18, 4.4, "art-bline-staged", rx=2.2)
               + T(fx + 98, 204, "B: working tree", "art-lab", 11)
               + R(fx + 180, 199, 10, 4.4, "art-bline-work", rx=2.2), "art-dim-result"))
    return svg(k, "".join(o), (400, 220))


def _p_safety_core():
    k = "safety-core"
    o = []
    rb = [halo(4, 10, 134, 202, "build", rx=8)]
    rb.append(R(14, 82, 58, 56, "art-frame-ink", rx=3))
    rb.append(P("M22 82v56", "art-line art-thin"))
    rb.append(T(46, 106, "one", "art-labi", 11.5, "middle"))
    rb.append(T(46, 121, "rulebook", "art-labi", 11.5, "middle"))
    outs = [(30, "AGENTS.md"), (110, "CLAUDE.md"), (190, "hooks")]
    for i, (y, name) in enumerate(outs):
        rb.append(plait((72, 110), (88, y - 4), c1=(84, 110), c2=(80, y - 4), amp=1.4, crossings=2, ends=False, delay=f"art-d{i}"))
        rb.append(T(92, y, name, "art-monoi", 12))
    o.append(G("".join(rb), "art-dim-written art-dim-hook"))
    o.append(L(158, 16, 158, 206, "art-hair"))
    x = 172
    o.append(T(x, 28, "Claude Haiku 4.5, 10 runs each", "art-lab", 11.5))
    o.append(T(x, 44, "■ = committed a made-up setting value", "art-lab", 11))
    rows = [("no rule", 10, "", "art-dim-hook"), ("written rule", 6, "written", "art-dim-hook"), ("hook", 0, "hook", "art-dim-written")]
    for j, (lab, n, st, dcls) in enumerate(rows):
        y = 78 + j * 46
        g = []
        if st:
            g.append(halo(x - 6, y - 18, 230, 44, st, rx=6))
        g.append(T(x, y, lab, "art-txt", 12.5))
        g.append(T(394, y, f"{n} of 10", "art-f" if n else "art-fink", 15, "end"))
        g.append(run_strip(x, y + 8, n, cell=15, gap=5.2))
        o.append(G("".join(g), dcls))
    return svg(k, "".join(o), (400, 220))


def _p_codemap():
    k = "codemap"
    o = []
    a, ra = _codefile(8, 10, 168, 104, 52, 2, heads=3, seed=3, ink_def=0)
    o.append(G(halo(4, 6, 176, 112, "file", rx=7) + a, "art-dim-text"))
    b, rb = _codefile(8, 128, 168, 82, 44, 1, heads=2, seed=6)
    o.append(G(b, "art-dim-text art-dim-file"))
    o.append(G(halo(108, rb[0] - 9, 50, 18, "callers", rx=5)
               + T(118, rb[0] + 4, "f()", "art-monoi", 12)
               + plait((140, rb[0]), (88, ra[0]), c1=(204, rb[0]), c2=(204, ra[0]), amp=2.2, crossings=4)
               + T(196, 132, "called by", "art-labi", 11.5, "end"),
               "art-dim-text art-dim-file"))
    # The same description, fetched as text.
    t = [halo(214, 6, 186, 208, "text", rx=7)]
    t.append(R(218, 10, 178, 200, "art-frame-ink", rx=4))
    t.append(T(228, 30, "as text, for agents", "art-lab", 11.5))
    rnd = random.Random(3)
    y = 50
    for h in range(3):
        t.append(bar(228, y, 26, "art-fill", 3.4))
        y += 12
        for _ in range(2):
            t.append(bar(228, y, 120 + 30 * rnd.random()))
            y += 10
        y += 8
    t.append(T(228, 186, "called by:", "art-mono", 11.5))
    t.append(bar(304, 182, 50, "art-bar art-bar-strong", 3.6))
    o.append(G("".join(t), "art-dim-file art-dim-callers"))
    o.append(G(plait((180, 60), (218, 60), amp=1.6, crossings=2, ends=False), "art-dim-file art-dim-callers"))
    return svg(k, "".join(o), (400, 220))


def _p_code_ontology_bridge():
    k = "code-ontology-bridge"
    o = []
    src = [R(8, 18, 74, 94, "art-frame", rx=3)]
    src.append(R(16, 26, 12, 14, "art-filetab", rx=1.5))
    src.append(T(34, 37, ".py", "art-mono", 12))
    for i, y in enumerate(range(54, 108, 12)):
        if i % 2 == 0:
            src.append(T(16, y + 4, "def", "art-monoi", 11))
            src.append(bar(42, y, 30))
        else:
            src.append(bar(24, y, 46))
    o.append(G("".join(src), "art-dim-study"))
    o.append(G(plait((82, 64), (128, 64), amp=1.8, crossings=2, ends=False)
               + T(105, 130, "static", "art-lab", 11, "middle")
               + T(105, 143, "analysis", "art-lab", 11, "middle"), "art-dim-study"))
    db = [halo(124, 10, 140, 112, "tables", rx=8)]
    cx, top = 158, 26
    db.append(P(f"M{cx - 26} {top}v64a26 8 0 0 0 52 0v-64", "art-frame-ink"))
    db.append(P(f"M{cx - 26} {top}a26 8 0 0 0 52 0a26 8 0 0 0 -52 0Z", "art-frame-ink"))
    db.append(P(f"M{cx - 26} {top + 32}a26 8 0 0 0 52 0", "art-line art-thin"))
    db.append(T(cx, 118, "DuckDB", "art-txt", 12, "middle"))
    for i, (tx, lab) in enumerate(((192, "functions"), (192, "calls"))):
        ty = 18 + i * 52
        db.append(R(tx, ty, 66, 44, "art-frame", rx=3))
        db.append(R(tx, ty, 66, 15, "art-tint", rx=3))
        db.append(T(tx + 33, ty + 11.5, lab, "art-labi", 11, "middle"))
        for r in range(2):
            yy = ty + 24 + r * 10
            if lab == "calls":
                db.append(bar(tx + 7, yy, 20) + P(f"M{tx + 31} {yy}h5", "art-line-q") + bar(tx + 40, yy, 18))
            else:
                db.append(bar(tx + 7, yy, 36 + 12 * r))
    o.append(G("".join(db), "art-dim-study"))
    # The text-to-SQL agent's recursive query.
    q = [halo(266, 6, 132, 116, "query", rx=8)]
    q.append(R(270, 10, 124, 108, "art-frame-ink", rx=4))
    q.append(T(278, 28, "text-to-SQL", "art-lab", 11))
    q.append(T(278, 46, "WITH RECURSIVE", "art-monoi", 11.5))
    q.append(T(278, 62, "callers AS (", "art-mono", 11.5))
    q.append(T(286, 78, "… UNION …", "art-monoq", 11.5))
    q.append(T(278, 94, ")", "art-mono", 11.5))
    q.append(T(278, 110, "all callers of f", "art-labi", 11))
    o.append(G("".join(q), "art-dim-tables art-dim-study"))
    o.append(G(plait((258, 64), (270, 64), amp=1, crossings=1, ends=False), "art-dim-study"))
    # The study: questions answered, of 12, averaged.
    s = [halo(4, 152, 394, 64, "study", rx=8)]
    x0, W = 108, 240
    s.append(T(8, 166, "questions answered, of 12", "art-lab", 11))
    for v in range(0, 13, 3):
        s.append(L(x0 + W * v / 12, 170, x0 + W * v / 12, 210, "art-hair"))
    s.append(T(8, 184, "with database", "art-txt", 12))
    s.append(R(x0, 175, W * 10.3 / 12, 12, "art-fill art-grow", rx=2))
    s.append(T(x0 + W * 10.3 / 12 + 6, 185, "10.3", "art-fink", 14))
    s.append(T(8, 206, "DeepSeek alone", "art-txt", 12))
    s.append(R(x0, 197, W * 3.2 / 12, 12, "art-barq art-grow", rx=2))
    s.append(T(x0 + W * 3.2 / 12 + 6, 207, "3.2", "art-f", 14))
    o.append(G("".join(s), "art-dim-tables art-dim-query"))
    return svg(k, "".join(o), (400, 220))


def _p_zenith():
    k = "zenith"
    o = [hatch(k)]
    pr = [halo(4, 8, 128, 132, "records", rx=8)]
    pr.append(T(10, 26, "28 practice problems", "art-lab", 11.5))
    for i in range(28):
        r, c = divmod(i, 7)
        pr.append(R(10 + c * 16.5, 38 + r * 16.5, 13, 13, "art-cell", rx=2))
    pr.append(T(10, 124, "missed-bug records", "art-labi", 12))
    o.append(G("".join(pr), "art-dim-result art-dim-timeouts"))
    o.append(G(plait((70, 132), (150, 182), c1=(70, 170), c2=(110, 182), amp=2, crossings=3, ends=False), "art-dim-result art-dim-timeouts"))
    o.append(G(R(150, 166, 128, 34, "art-frame-ink", rx=4)
               + T(214, 188, "DeepSeek V4.1 Flash", "art-txt", 12, "middle"), "art-dim-timeouts"))
    x0, W = 150, 210
    res = [halo(142, 8, 254, 120, "result", rx=8)]
    res.append(T(x0, 26, "bugs caught, 58 held-out problems", "art-lab", 11.5))
    for v in (0, 25, 50, 75, 100):
        res.append(L(x0 + W * v / 100, 36, x0 + W * v / 100, 114, "art-hair"))
        res.append(T(x0 + W * v / 100, 124, f"{v}", "art-lab", 10.5, "middle"))
    w69, w77 = W * 0.69, W * 0.77
    res.append(R(x0, 44, w69, 22, "art-barq art-grow", rx=2))
    res.append(T(x0 + w69 + 8, 61, "69%", "art-f", 17))
    res.append(T(x0 + 6, 59.5, "before", "art-chipt-q", 11.5))
    res.append(G(R(x0, 80, w69, 26, "art-fill", rx=2)
                 + R(x0 + w69, 80, (w77 - w69) / 2, 26, "art-fill"), "art-grow art-d1"))
    res.append(T(x0 + 6, 97.5, "with records", "art-chipt", 11.5))
    res.append(T(x0 + w77 + 8, 100, "77%", "art-fink", 22))
    o.append(G("".join(res), "art-dim-records"))
    hx = x0 + w69 + (w77 - w69) / 2
    tm = [halo(hx - 8, 74, (w77 - w69) / 2 + 16, 38, "timeouts", rx=4)]
    tm.append(R(hx, 80, (w77 - w69) / 2, 26, "art-hatchbar art-grow art-d2", extra=hatch_fill(k)))
    tm.append(R(hx, 80, (w77 - w69) / 2, 26, "art-chipline"))
    tm.append(P(f"M{_f(hx + 2)} 110v26", "art-line art-thin"))
    tm.append(T(hx + 8, 150, "≈ half of the rise:", "art-labi", 12))
    tm.append(T(hx + 8, 165, "timeouts", "art-labi", 12))
    o.append(G("".join(tm), "art-dim-records"))
    return svg(k, "".join(o), (400, 220))


def _p_funnel():
    k = "funnel"
    o = []
    lp = [halo(2, 58, 80, 90, "proof", rx=8)]
    lp.append(R(8, 64, 68, 78, "art-frame-ink", rx=4))
    lp.append(T(42, 92, "#257", "art-f", 18, "middle"))
    lp.append(T(42, 112, "Erdős", "art-lab", 11.5, "middle"))
    lp.append(chip(16, 118, 52, "Lean ✓", size=11.5, h=17))
    o.append(G("".join(lp)))
    base, sc = 150, 0.5
    items = [(104, 152, "152 pages", "research record"), (176, 26, "26 pages", "expert paper"),
             (248, 16, "16 pages", "exposition")]
    pg = [halo(96, 60, 222, 132, "pages", rx=8)]
    for i, (x, n, lab, what) in enumerate(items):
        pg.append(plait((76, 103), (x + 4, base - n * sc - 4), c1=(88, 103), c2=(x - 10, base - n * sc - 4),
                        amp=1.6, crossings=2, ends=False, delay=f"art-d{i}"))
        pg.append(G(pile(x, base, 60, n, sc, every=8), f"art-rise art-d{i + 1}"))
        pg.append(T(x + 30, 170, lab, "art-txt", 12.5, "middle"))
        pg.append(T(x + 30, 186, what, "art-lab", 11.5, "middle"))
    o.append(G("".join(pg), "art-dim-proof art-dim-video"))
    o.append(T(104, 34, "AI, following written instructions", "art-lab", 11.5))
    v = [halo(318, 60, 80, 132, "video", rx=8)]
    v.append(plait((76, 103), (322, 118), c1=(160, 30), c2=(300, 60), amp=1.8, crossings=5, ends=False, delay="art-d3"))
    v.append(filmframe(322, 100, 72, 50, arrows=False))
    v.append(P("M352 114l14 11-14 11Z", "art-fill"))
    v.append(T(358, 170, "video", "art-txt", 12.5, "middle"))
    o.append(G("".join(v), "art-dim-proof art-dim-pages"))
    o.append(T(8, 210, "stacks drawn to scale: 1 line = 8 pages", "art-lab", 11))
    return svg(k, "".join(o), (400, 220))


def _p_narration_ir():
    k = "narration-ir"
    o = []
    pl = [halo(4, 6, 184, 106, "plan quotes", rx=8)]
    pl.append(R(8, 10, 176, 98, "art-frame-ink", rx=4))
    pl.append(T(18, 28, "plan for one sentence", "art-lab", 11.5))
    pl.append(T(18, 50, "meaning", "art-txt", 12))
    pl.append(bar(84, 46, 86))
    pl.append(T(18, 72, "cue", "art-txt", 12))
    pl.append(R(52, 63, 30, 11, "art-fill", rx=2))
    pl.append(T(88, 72, "→ arrow 3 on", "art-labi", 12))
    pl.append(T(18, 94, "quote", "art-txt", 12))
    pl.append(G(R(62, 85, 74, 12, "art-tint", rx=2) + bar(66, 91, 64, "art-bar art-bar-ink")
                + tick(152, 91, 1), "art-dim-cue"))
    o.append(G("".join(pl)))
    # Picture: the third arrow turns on at the cue word.
    pic = [halo(204, 6, 194, 106, "cue", rx=8)]
    pic.append(R(208, 10, 186, 98, "art-frame", rx=4))
    pic.append(T(218, 28, "picture", "art-lab", 11.5))
    for i, x in enumerate((236, 288, 340)):
        cls = "art-line art-cuearrow" if i == 2 else "art-line-q"
        pic.append(P(f"M{x} 64h30m-7-7 7 7-7 7", cls))
        pic.append(T(x + 15, 92, f"{i + 1}", "art-lab", 11, "middle"))
    o.append(G("".join(pic), "art-dim-quotes"))
    # The recording: one spoken sentence, word by word.
    rec = []
    rec.append(waveform(10, 390, 142, 9, seed=8))
    widths = [26, 40, 20, 44, 30, 34, 22, 40, 30, 38, 26]
    x = 10
    cx = 0
    for i, w in enumerate(widths):
        cue = i == 8
        rec.append(R(x, 162, w, 12, "art-fill art-cueword" if cue else "art-word", rx=2))
        if cue:
            cx = x + w / 2
        x += w + 4.7
    rec.append(T(10, 196, "recorded words", "art-lab", 11.5))
    rec.append(T(390, 196, "time →", "art-lab", 11.5, "end"))
    o.append(G("".join(rec), "art-dim-quotes"))
    o.append(G(P(f"M{_f(cx)} 160V{_f(108)}", "art-line art-dashed")
               + T(cx - 8, 126, "named word", "art-labi", 11.5, "end"), "art-dim-plan art-dim-quotes"))
    o.append(G(T(196, 214, "", "art-lab", 1)))
    q = [halo(4, 118, 392, 0.1, "quotes")]
    o.append(G("".join(q)))
    o.append(G(T(204, 214, "quote found in its source file ✓", "art-labi", 11.5), "art-hide-plan art-hide-cue"))
    return svg(k, "".join(o), (400, 220))


_DRAW = {
    "research": _door_research, "proofs": _door_proofs, "assistants": _door_assistants,
    "explaining": _door_explaining, "code": _door_code, "testing": _door_testing,
    "maths": _p_maths, "quartic": _p_quartic, "lean-exposition": _p_lean_exposition,
    "proof-reader": _p_proof_reader, "atlas": _p_atlas, "formal-verification": _p_formal_verification,
    "agent-trace": _p_agent_trace, "one-checkout": _p_one_checkout, "safety-core": _p_safety_core,
    "codemap": _p_codemap, "code-ontology-bridge": _p_code_ontology_bridge, "zenith": _p_zenith,
    "funnel": _p_funnel, "narration-ir": _p_narration_ir,
}


def art_svg(kind: str) -> str:
    """One literal drawing, as an inline <svg>. Unknown kinds raise KeyError."""
    return _DRAW[kind]()


__all__ = ["art_svg", "DOOR_KINDS", "PROJECT_KINDS", "DEMO_STATES"]
