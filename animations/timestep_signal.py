"""Figure: timestep-signal, the flow-matching timestep is a PER-TOKEN input that
tells the model how noisy each action step is. Set the prefix to clean, leave the
postfix noisy. (Essence of the paper's Fig. 2.)"""

from manim import *

from common import C_FROZEN, C_MUTED, C_NOISE, C_TEXT, step_cell, styled, title

N, K = 6, 2
BW, BH = 0.34, 1.1
GY = -1.5


class TimestepSignal(Scene):
    def construct(self):
        styled(self)
        head = title("The timestep is a per-token 'how noisy am I?' signal").scale(0.52).to_edge(UP, buff=0.45)
        self.play(FadeIn(head))

        # model box
        box = RoundedRectangle(width=5.4, height=0.8, corner_radius=0.14,
                               stroke_color=C_MUTED, stroke_width=2, fill_opacity=0).shift(UP * 1.9)
        box_t = Text("action model", color=C_TEXT, font_size=24).move_to(box)
        self.play(Create(box), FadeIn(box_t))

        # token row
        cells = VGroup(*[
            step_cell("frozen" if i < K else "noise", label=None).scale(0.9)
            for i in range(N)
        ]).arrange(RIGHT, buff=0.28).shift(UP * 0.35)
        self.play(LaggedStart(*[FadeIn(c) for c in cells], lag_ratio=0.06))
        # tokens feed up into the model
        ups = VGroup(*[Arrow(c.get_top(), [c.get_x(), box.get_bottom()[1], 0], buff=0.06,
                             color=C_MUTED, stroke_width=2, max_tip_length_to_length_ratio=0.25) for c in cells])
        self.play(LaggedStart(*[GrowArrow(a) for a in ups], lag_ratio=0.05))

        # per-token timestep gauge below each token (fill = noise level)
        sig = ValueTracker(1.0)
        getters = [(lambda: 0.0) if i < K else (lambda: sig.get_value()) for i in range(N)]

        def gauge(base, getter):
            h = max(0.001, BH * getter())
            return (Rectangle(width=BW * 0.8, height=h, stroke_width=0, fill_color=C_NOISE, fill_opacity=0.65)
                    .move_to(base.get_bottom()).shift(UP * h / 2))

        bases, fills, arrows = VGroup(), VGroup(), VGroup()
        for i, c in enumerate(cells):
            frozen = i < K
            base = RoundedRectangle(width=BW, height=BH, corner_radius=0.05,
                                    stroke_color=(C_FROZEN if frozen else C_NOISE), stroke_width=2,
                                    fill_opacity=0).move_to([c.get_x(), GY, 0])
            bases.add(base)
            fills.add(always_redraw(lambda b=base, g=getters[i]: gauge(b, g)))
            arrows.add(Arrow(base.get_top(), c.get_bottom(), buff=0.06, color=C_MUTED,
                             stroke_width=2, max_tip_length_to_length_ratio=0.3))
        tau = Text("τ  (flow-matching timestep = noise level)", color=C_TEXT, font_size=22).next_to(bases, DOWN, buff=0.3)
        self.play(FadeIn(bases), FadeIn(arrows), FadeIn(tau))
        self.add(fills)

        pre_lab = Text("prefix: τ = clean", color=C_FROZEN, font_size=20).next_to(VGroup(*bases[:K]), LEFT, buff=0.3)
        post_lab = Text("postfix: τ noisy, denoising", color=C_NOISE, font_size=20).next_to(VGroup(*bases[K:]), RIGHT, buff=0.3)
        self.play(FadeIn(pre_lab), FadeIn(post_lab))
        self.wait(0.4)
        self.play(sig.animate.set_value(0.0), run_time=3.5, rate_func=linear)
        self.wait(1.0)
