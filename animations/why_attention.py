"""Figure: why-attention, the crux of WHY fixing the prefix smooths the rest.

The postfix is still denoised, so why isn't it jerky? Because the policy is a
transformer: every postfix token attends to the clean, fixed prefix tokens, so
the velocities it predicts continue out of the committed actions. The loss is
masked to the postfix (the prefix is given, not predicted), which trains exactly
those attention pathways.
"""

from manim import *

from common import (
    C_A,
    C_CLEAN,
    C_FROZEN,
    C_MUTED,
    C_NOISE,
    C_TEXT,
    C_WARN,
    step_cell,
    styled,
    title,
)

N, K = 6, 2  # 6 action tokens: first K are the clean committed prefix


class WhyAttention(Scene):
    def construct(self):
        styled(self)
        head = title("Why fixing the prefix smooths the rest: self-attention").scale(0.5).to_edge(UP, buff=0.4)
        self.play(FadeIn(head))

        # --- token row -----------------------------------------------------
        cells = VGroup(*[
            step_cell("frozen" if i < K else "noise", label=None).scale(0.95)
            for i in range(N)
        ]).arrange(RIGHT, buff=0.5).shift(UP * 1.55)
        self.play(LaggedStart(*[FadeIn(c) for c in cells], lag_ratio=0.08))

        pre_lab = Text("clean, fixed  (no loss)", color=C_FROZEN, font_size=20).next_to(VGroup(*cells[:K]), UP, buff=0.18)
        post_lab = Text("denoising  (loss here)", color=C_NOISE, font_size=20).next_to(VGroup(*cells[K:]), UP, buff=0.18)
        self.play(FadeIn(pre_lab), FadeIn(post_lab))
        self.wait(0.3)

        # --- one postfix token attends to every prefix token ---------------
        focus = cells[K]  # first postfix step
        ring = SurroundingRectangle(focus, color=C_NOISE, buff=0.06, stroke_width=3)
        self.play(Create(ring))
        att = VGroup(*[
            CurvedArrow(focus.get_top() + UP * 0.03, cells[j].get_top() + UP * 0.03,
                        angle=-0.9, color=C_CLEAN, stroke_width=3, tip_length=0.16)
            for j in range(K)
        ])
        att_lab = Text("attends to the clean prefix", color=C_CLEAN, font_size=20).next_to(cells, DOWN, buff=0.25)
        self.play(LaggedStart(*[Create(a) for a in att], lag_ratio=0.2), FadeIn(att_lab))
        self.wait(0.4)

        # ...and so does every other postfix step (faint fan)
        faint = VGroup()
        for i in range(K + 1, N):
            for j in range(K):
                faint.add(CurvedArrow(cells[i].get_top() + UP * 0.03, cells[j].get_top() + UP * 0.03,
                                      angle=-0.9, color=C_CLEAN, stroke_width=1.5, tip_length=0.1).set_opacity(0.35))
        every = Text("every postfix step does the same", color=C_MUTED, font_size=18).next_to(att_lab, DOWN, buff=0.12)
        self.play(LaggedStart(*[Create(a) for a in faint], lag_ratio=0.03), FadeIn(every))
        self.wait(0.5)
        self.play(FadeOut(att), FadeOut(faint), FadeOut(ring), FadeOut(att_lab), FadeOut(every))

        # --- the payoff: velocities continue the prefix instead of jumping --
        ax = Axes(x_range=[0, 6], y_range=[0, 2.4], x_length=8.2, y_length=2.2,
                  axis_config={"color": C_MUTED, "include_tip": False, "include_numbers": False}).shift(DOWN * 1.4)

        def pre(t):
            return 1.0 + 0.16 * t

        seam_x = 3.0
        seam_y = pre(seam_x)
        cont = ax.plot(pre, x_range=[0, seam_x], color=C_FROZEN, stroke_width=5)
        cont_lab = Text("committed prefix (fixed)", color=C_FROZEN, font_size=18).next_to(ax.c2p(1.0, pre(1.0)), UP, buff=0.1)
        self.play(Create(cont), FadeIn(cont_lab))

        # free postfix: denoised without conditioning -> jumps at the seam
        free = ax.plot(lambda t: (seam_y - 0.5) + 0.16 * (t - seam_x), x_range=[seam_x, 6], color=C_WARN, stroke_width=4).set_opacity(0.7)
        jump = DashedLine(ax.c2p(seam_x, seam_y), ax.c2p(seam_x, seam_y - 0.5), color=C_WARN, stroke_width=3)
        jerk_lab = Text("jerk", color=C_WARN, font_size=18).next_to(jump, RIGHT, buff=0.08)
        self.play(Create(free), Create(jump), FadeIn(jerk_lab))
        self.wait(0.6)

        # conditioned postfix: attention pulls it to continue the prefix
        smooth = ax.plot(lambda t: seam_y + 0.16 * (t - seam_x), x_range=[seam_x, 6], color=C_CLEAN, stroke_width=5)
        smooth_lab = Text("The postfix continues the prefix, no jerk", color=C_CLEAN, font_size=28, weight=BOLD).next_to(ax, DOWN, buff=0.35)
        self.play(FadeOut(free), FadeOut(jump), FadeOut(jerk_lab), Create(smooth), FadeIn(smooth_lab))
        self.wait(3.2)
