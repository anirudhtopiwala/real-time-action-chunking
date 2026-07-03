"""Figure: action-delay, animated version of the paper's Fig. 1.

Two overlapping chunks on a controller timeline; sweep the inference delay d to
show the committed prefix (green) grow/shrink while the postfix (amber) is
generated. d is both the delay and the number of steps we condition on, bounded
by d <= H - s.  Adapted from Black et al., arXiv:2512.05964, Fig. 1.
"""

from manim import *

from common import C_FROZEN, C_MUTED, C_NOISE, C_TEXT, styled, title

S, H = 4, 8          # s = execution horizon, H = prediction horizon
TOT = S + H          # cells span t-s .. t+H
CW = 0.8             # cell width
ROW_Y = 0.4


class ActionDelay(Scene):
    def construct(self):
        styled(self)
        head = title("Action delay = how many steps you condition on").scale(0.56).to_edge(UP, buff=0.5)
        self.play(FadeIn(head))

        cells = VGroup(*[
            Rectangle(width=CW, height=CW, stroke_color=C_MUTED, stroke_width=1.5, fill_opacity=0)
            for _ in range(TOT)
        ]).arrange(RIGHT, buff=0).move_to(ORIGIN).shift(UP * ROW_Y)
        left = cells[0].get_left()[0]

        def xedge(i):
            return left + i * CW

        def color_for(i, d):
            if i < S:
                return C_MUTED, 0.18            # previous chunk, already executed
            return (C_FROZEN, 0.85) if (i - S) < d else (C_NOISE, 0.8)

        # start with the whole current chunk still "to generate" (amber), prev faint
        for i in range(TOT):
            col, op = color_for(i, 0)
            cells[i].set_fill(col, op).set_stroke(col if i >= S else C_MUTED)
        self.play(LaggedStart(*[FadeIn(c) for c in cells], lag_ratio=0.04))

        # brackets
        prev_br = Brace(VGroup(*cells[:S]), UP, color=C_MUTED)
        prev_t = Text("previous chunk", color=C_MUTED, font_size=22).next_to(prev_br, UP, buff=0.1)
        cur_br = Brace(VGroup(*cells[S:]), UP, color=C_TEXT)
        cur_t = Text("current chunk", color=C_TEXT, font_size=22).next_to(cur_br, UP, buff=0.1)
        self.play(FadeIn(prev_br), FadeIn(prev_t), FadeIn(cur_br), FadeIn(cur_t))

        # static markers
        my = cells[0].get_bottom()[1] - 0.15
        def marker(i, label):
            tick = Line([xedge(i), my, 0], [xedge(i), my - 0.28, 0], color=C_MUTED, stroke_width=2)
            lab = Text(label, color=C_TEXT, font_size=22).next_to(tick, DOWN, buff=0.1)
            return VGroup(tick, lab)
        m_ts = marker(0, "t−s")
        m_t = marker(S, "t")
        m_tsh = marker(H, "t−s+H")   # index t-s+H = (S+H)-S = H
        m_tH = marker(TOT, "t+H")
        self.play(*[FadeIn(m) for m in (m_ts, m_t, m_tsh, m_tH)])

        # overlap bracket (valid prefix range)
        ov_br = Brace(VGroup(*cells[S:H]), DOWN, color=C_FROZEN).shift(DOWN * 0.9)
        ov_t = Text("valid prefix:  d ≤ H − s", color=C_FROZEN, font_size=22).next_to(ov_br, DOWN, buff=0.1)

        # dynamic t+d marker
        tick_y0, tick_y1 = my, my - 0.28
        tplusd = VGroup(
            Line([xedge(S + 1), tick_y0, 0], [xedge(S + 1), tick_y1, 0], color=C_FROZEN, stroke_width=3),
            Text("t+d", color=C_FROZEN, font_size=22),
        )
        tplusd[1].next_to(tplusd[0], DOWN, buff=0.1)

        def set_d(d, run=0.9):
            anims = []
            for i in range(S, TOT):
                col, op = color_for(i, d)
                anims.append(cells[i].animate.set_fill(col, op).set_stroke(col))
            anims.append(tplusd[0].animate.move_to([xedge(S + d), (tick_y0 + tick_y1) / 2, 0]))
            anims.append(tplusd[1].animate.move_to([xedge(S + d), tick_y1 - 0.2, 0]))
            self.play(*anims, run_time=run)

        cap = Text("while the model computes the next chunk, the robot executes d steps,\n"
                   "those d committed actions become the clean prefix",
                   color=C_TEXT, font_size=22, line_spacing=0.8).to_edge(DOWN, buff=0.35)
        self.play(FadeIn(tplusd), FadeIn(ov_br), FadeIn(ov_t), FadeIn(cap))
        set_d(1, run=0.6)

        # sweep the delay
        for d in [2, 3, 4, 2, 3]:
            self.play(Wait(0.15))
            set_d(d)

        self.wait(1.2)
