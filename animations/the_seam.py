"""Figure: the-seam, chunk B is generated ahead of A, overlaps A's tail, and
extends beyond it. Jerk at the handoff, then the smooth fix."""

import numpy as np
from manim import *

from common import C_A, C_B, C_FROZEN, C_MUTED, C_TEXT, C_WARN, styled


class TheSeam(Scene):
    def construct(self):
        styled(self)
        ax = Axes(
            x_range=[0, 12, 2], y_range=[0, 3, 1], x_length=11, y_length=4.0,
            axis_config={"color": C_MUTED, "include_tip": False, "include_numbers": False},
        ).shift(DOWN * 0.3)
        xlab = Text("time", color=C_TEXT, font_size=24).next_to(ax.x_axis, DOWN, buff=0.15).align_to(ax.x_axis, RIGHT)
        ylab = Text("gripper height", color=C_TEXT, font_size=24).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.15)
        self.play(Create(ax), FadeIn(xlab), FadeIn(ylab))

        fA = lambda t: 1.3 + 0.45 * np.sin(0.7 * t)
        th = 6.0  # handoff time

        cA = ax.plot(fA, x_range=[0, 8], color=C_A, stroke_width=5)
        labA = Text("chunk A", color=C_A, font_size=26).next_to(ax.c2p(2, fA(2)), UP, buff=0.3)
        self.play(Create(cA), FadeIn(labA))

        # chunk B: generated ahead, overlaps A on [4,8], extends to 12
        jump = 0.55
        fBj = lambda t: fA(t) + jump
        cBj = ax.plot(fBj, x_range=[4, 12], color=C_B, stroke_width=5)
        labB = Text("chunk B (ahead)", color=C_B, font_size=26).next_to(ax.c2p(10.5, fBj(10.5)), UP, buff=0.3)
        self.play(Create(cBj), FadeIn(labB))

        ov = DashedLine(ax.c2p(4, 0.2), ax.c2p(8, 0.2), color=C_MUTED, stroke_width=3)
        ov_lab = Text("overlap", color=C_MUTED, font_size=22).next_to(ov, DOWN, buff=0.08)
        self.play(FadeIn(ov), FadeIn(ov_lab))

        p_a, p_b = ax.c2p(th, fA(th)), ax.c2p(th, fBj(th))
        gap = DashedLine(p_a, p_b, color=C_WARN, stroke_width=5)
        ring = Circle(radius=0.38, color=C_WARN, stroke_width=4).move_to((np.array(p_a) + np.array(p_b)) / 2)
        jl = Text("jerk!", color=C_WARN, font_size=30, weight=BOLD).next_to(ring, RIGHT, buff=0.2)
        self.play(Create(gap), Create(ring), FadeIn(jl))
        self.wait(1.2)

        cBs = ax.plot(fA, x_range=[4, 12], color=C_B, stroke_width=5)
        self.play(
            FadeOut(gap), FadeOut(ring), FadeOut(jl),
            Transform(cBj, cBs),
            labB.animate.next_to(ax.c2p(10.5, fA(10.5)), UP, buff=0.3),
            run_time=1.5,
        )
        ok = Text("smooth handoff", color=C_FROZEN, font_size=30, weight=BOLD).to_edge(DOWN, buff=0.3)
        self.play(FadeIn(ok))
        self.wait(1.5)
