"""Shared style and primitives for the action-chunk-adherence figures.

Render any scene with, e.g.:
    manim -qm fig01_the_seam.py TheSeam
(run from this directory so `common` is importable).
"""

import numpy as np
from manim import *

# ---------------------------------------------------------------------------
# Palette, one consistent visual language across every figure.
# ---------------------------------------------------------------------------
C_BG = "#0E1117"        # near-black background (the 3b1b look)
C_NOISE = "#F2A341"     # amber  = noisy step / pure noise
C_CLEAN = "#4FC3F7"     # blue   = clean / finished action
C_FROZEN = "#34D399"    # green  = committed / frozen / locked prefix
C_A = "#7AA2F7"         # chunk A (the previous chunk)
C_B = "#F2A341"         # chunk B (the next chunk)
C_MUTED = "#5C6370"     # axes, secondary lines
C_TEXT = "#E6E6E6"      # primary text
C_WARN = "#EF6F6C"      # warnings / "never happens"

CELL = 0.62             # step-cell side length
GAP = 0.16             # gap between cells


def styled(scene):
    """Apply the shared dark background to a scene."""
    scene.camera.background_color = C_BG


def caption(text, color=C_TEXT, size=30):
    return Text(text, color=color, font_size=size)


def title(text, size=40):
    return Text(text, color=C_TEXT, font_size=size, weight=BOLD)


def lock_icon(scale=0.18, color=C_FROZEN):
    """A tiny padlock glyph (shackle + body)."""
    body = RoundedRectangle(width=1.0, height=0.8, corner_radius=0.12,
                            stroke_width=0, fill_color=color, fill_opacity=1.0)
    shackle = Arc(radius=0.32, start_angle=0, angle=PI, stroke_color=color,
                  stroke_width=6).next_to(body, UP, buff=-0.06)
    keyhole = Dot(radius=0.07, color=C_BG).move_to(body.get_center())
    return VGroup(shackle, body, keyhole).scale(scale)


def step_cell(state="noise", label=None, level=None):
    """One action step as a rounded square, colored by state.

    state: "noise" (amber), "clean" (blue), "frozen" (green committed).
    level: optional 0..1 noise level -> draws an amber fill bar from the top.
    """
    color = {"noise": C_NOISE, "clean": C_CLEAN, "frozen": C_FROZEN}[state]
    cell = RoundedRectangle(width=CELL, height=CELL, corner_radius=0.08,
                            stroke_color=color, stroke_width=2.5,
                            fill_color=color, fill_opacity=0.22)
    group = VGroup(cell)
    if level is not None:
        # amber fill from the top representing how noisy the step is
        h = max(0.001, CELL * level)
        fill = Rectangle(width=CELL, height=h, stroke_width=0,
                         fill_color=C_NOISE, fill_opacity=0.55)
        fill.align_to(cell, UP)
        group.add(fill)
    if label is not None:
        group.add(Text(str(label), color=C_TEXT, font_size=20).move_to(cell))
    return group


def step_row(n, states=None, labels=True):
    """A horizontal row of n step cells. `states` is a list of state strings."""
    states = states or ["noise"] * n
    cells = VGroup()
    for i in range(n):
        lab = i if labels else None
        cells.add(step_cell(state=states[i], label=lab))
    cells.arrange(RIGHT, buff=GAP)
    return cells


def legend(entries, size=22):
    """entries: list of (color, text). Returns a horizontal legend VGroup."""
    items = VGroup()
    for color, text in entries:
        swatch = Square(side_length=0.22, stroke_width=0,
                        fill_color=color, fill_opacity=1.0)
        items.add(VGroup(swatch, Text(text, color=C_TEXT, font_size=size)
                         ).arrange(RIGHT, buff=0.12))
    items.arrange(RIGHT, buff=0.5)
    return items


# ---------------------------------------------------------------------------
# Handoff-trajectory helper, shows the A→B motion each conditioning method
# produces (the "additional signal" beside the step-cells).
# ---------------------------------------------------------------------------
def traj_fA(t):
    return 1.4 + 0.5 * np.sin(0.5 * t)


# Chunk A spans [_A0, _A1]. Chunk B is the NEXT chunk, generated ahead: it starts
# at _B0 (offset from A's start) and overlaps A's tail on [_B0, _A1].
_A0, _A1, _B0 = 0.0, 8.0, 4.0


def traj_fB(method, t):
    a = traj_fA(t)
    ov1 = _A1  # end of the overlap = the last committed step / handoff point
    if method == "full-prefix":
        # matches A across the whole overlap, then the two part ways
        return a if t <= ov1 else a + 0.32 * (t - ov1)
    if method == "single-action":
        # free through the overlap; meets A at one committed step (ov1), then diverges
        return a + 0.6 * np.tanh((t - ov1) / 2.0)
    return a


def add_method_trajectory(scene, method):
    """Chunk A vs chunk B motion. B is the next chunk: it starts ahead of A (at
    _B0) and overlaps A's tail; how it relates in the overlap depends on `method`."""
    ax = Axes(
        x_range=[0, 12], y_range=[0, 3], x_length=7.0, y_length=2.0,
        axis_config={"color": C_MUTED, "include_tip": False, "include_numbers": False},
    ).shift(DOWN * 2.05)

    lo, hi = ax.c2p(_B0, 0), ax.c2p(_A1, 3)
    band = Rectangle(width=hi[0] - lo[0], height=hi[1] - lo[1], stroke_width=0,
                     fill_color=C_MUTED, fill_opacity=0.12).move_to([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0])
    band_t = Text("overlap (committed prefix)", color=C_MUTED, font_size=18).move_to(band).align_to(band, UP).shift(DOWN * 0.12)

    cA = ax.plot(lambda t: traj_fA(t), x_range=[_A0, _A1], color=C_A, stroke_width=4)
    cA_ghost = ax.plot(lambda t: traj_fA(t), x_range=[_A1, 12], color=C_A, stroke_width=3).set_opacity(0.3)
    cB = ax.plot(lambda t: traj_fB(method, t), x_range=[_B0, 12], color=C_B, stroke_width=4)
    aL = Text("chunk A", color=C_A, font_size=20).next_to(ax.c2p(1.6, traj_fA(1.6)), UP, buff=0.12)
    bL = Text("chunk B", color=C_B, font_size=20).next_to(ax.c2p(11.4, traj_fB(method, 11.4)), RIGHT, buff=0.05)
    bstart = Dot(ax.c2p(_B0, traj_fB(method, _B0)), color=C_B, radius=0.07)

    scene.play(Create(ax), FadeIn(band), FadeIn(band_t))
    scene.play(Create(cA), FadeIn(cA_ghost), FadeIn(aL))
    scene.play(Create(cB), FadeIn(bstart), FadeIn(bL))

    notes = {
        "single-action": ("B is free through the overlap, meets A at one committed step, then diverges", C_WARN),
        "full-prefix": ("B matches A across the whole overlap, then they part ways", C_FROZEN),
    }
    txt, col = notes[method]
    if method == "single-action":
        scene.play(FadeIn(Dot(ax.c2p(_A1, traj_fA(_A1)), color=C_FROZEN, radius=0.08)))
    scene.play(FadeIn(Text(txt, color=col, font_size=20).next_to(ax, DOWN, buff=0.1)))
    scene.wait(1.2)
