"""Figure: soft-target, fade the prefix's influence; trajectory eases away smoothly."""

from manim import *

from common import C_FROZEN, C_TEXT, add_method_trajectory, step_row, styled, title


class SoftTarget(Scene):
    def construct(self):
        styled(self)
        head = title("Soft target: fade, don't clamp").scale(0.56).to_edge(UP, buff=0.4)
        N, W = 8, 4
        weights = [1.0, 0.5, 0.25, 0.125]
        row = step_row(N, ["noise"] * N).shift(UP * 1.2)
        self.play(FadeIn(head), FadeIn(row))

        maxh = 0.95
        bars = VGroup()
        for i, w in enumerate(weights):
            bar = Rectangle(width=0.3, height=maxh * w, stroke_width=0, fill_color=C_FROZEN, fill_opacity=0.85)
            bar.next_to(row[i], UP, buff=0.12, aligned_edge=DOWN)
            wlab = Text(f"{w:g}", color=C_TEXT, font_size=16).next_to(bar, UP, buff=0.06)
            bars.add(VGroup(bar, wlab))
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.15) for b in bars], lag_ratio=0.15))

        alpha = lambda w: f"{round((0.12 + 0.4 * w) * 255):02x}"
        self.play(*[row[i][0].animate.set_stroke(C_FROZEN).set_fill(C_FROZEN + alpha(weights[i])) for i in range(W)])

        add_method_trajectory(self, "soft")
