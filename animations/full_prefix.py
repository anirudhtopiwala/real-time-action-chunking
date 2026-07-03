"""Figure: full-prefix, freeze every committed step; trajectory shows smooth handoff."""

from manim import *

from common import (C_FROZEN, C_NOISE, add_method_trajectory, lock_icon, step_cell, step_row, styled, title)


class FullPrefix(Scene):
    def construct(self):
        styled(self)
        head = title("Full prefix: freeze every committed step").scale(0.52).to_edge(UP, buff=0.4)
        N, K = 8, 3
        row = step_row(N, ["noise"] * N).shift(UP * 1.6)
        self.play(FadeIn(head), FadeIn(row))

        self.play(LaggedStart(*[Transform(row[i], step_cell("frozen", label=i).move_to(row[i])) for i in range(K)], lag_ratio=0.1))
        locks = VGroup(*[lock_icon(scale=0.12).move_to(row[i].get_corner(UR)) for i in range(K)])
        self.play(FadeIn(locks))

        prefix, tail = VGroup(*row[:K]), VGroup(*row[K:])
        br1 = Brace(prefix, DOWN, color=C_FROZEN)
        t1 = Text("frozen prefix", color=C_FROZEN, font_size=20).next_to(br1, DOWN, buff=0.1)
        br2 = Brace(tail, DOWN, color=C_NOISE)
        t2 = Text("denoised tail", color=C_NOISE, font_size=20).next_to(br2, DOWN, buff=0.1)
        self.play(FadeIn(br1), FadeIn(t1), FadeIn(br2), FadeIn(t2))
        self.play(LaggedStart(*[Transform(row[i], step_cell("clean", label=i).move_to(row[i])) for i in range(K, N)], lag_ratio=0.08), run_time=1.4)

        add_method_trajectory(self, "target")
