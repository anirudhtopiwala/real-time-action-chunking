"""Figure: single-action, condition on one committed step; trajectory shows continuity at one point only."""

from manim import *

from common import add_method_trajectory, lock_icon, step_cell, step_row, styled, title


class SingleAction(Scene):
    def construct(self):
        styled(self)
        head = title("Single action: condition on one committed step").scale(0.52).to_edge(UP, buff=0.4)
        N, anchor = 8, 7
        row = step_row(N, ["noise"] * N).shift(UP * 1.6)
        self.play(FadeIn(head), FadeIn(row))

        self.play(Transform(row[anchor], step_cell("frozen", label=anchor).move_to(row[anchor])))
        lock = lock_icon(scale=0.13).move_to(row[anchor].get_corner(UR))
        self.play(FadeIn(lock))
        anims = [Transform(row[i], step_cell("clean", label=i).move_to(row[i])) for i in range(N) if i != anchor]
        self.play(LaggedStart(*anims, lag_ratio=0.08), run_time=1.5)

        add_method_trajectory(self, "anchor")
