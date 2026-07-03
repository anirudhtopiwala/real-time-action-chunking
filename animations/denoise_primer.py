"""Figure: denoise-primer, a step descends the noise line from 1 to 0."""

from manim import *

from common import C_CLEAN, C_MUTED, C_NOISE, C_TEXT, styled, title


class DenoisePrimer(Scene):
    def construct(self):
        styled(self)
        head = title("How a step gets denoised").scale(0.6).to_edge(UP, buff=0.5)
        self.play(FadeIn(head))

        top, bot = UP * 2.3, DOWN * 2.3
        axis = Line(bot, top, color=C_MUTED, stroke_width=3)
        noise_lab = Text("pure noise  (1)", color=C_NOISE, font_size=26).next_to(top, RIGHT, buff=0.4)
        clean_lab = Text("clean action  (0)", color=C_CLEAN, font_size=26).next_to(bot, RIGHT, buff=0.4)
        self.play(Create(axis), FadeIn(noise_lab), FadeIn(clean_lab))

        def pos(level):
            return bot + (top - bot) * level

        dot = Dot(pos(1.0), color=C_NOISE, radius=0.16)
        lvl = lambda: (dot.get_center()[1] - bot[1]) / (top[1] - bot[1])
        val = always_redraw(lambda: Text(f"{lvl():.2f}", color=C_TEXT, font_size=30).next_to(dot, LEFT, buff=0.4))
        self.play(FadeIn(dot), FadeIn(val))

        # Euler update, with the timestep τ shown live as the dot (the slider) descends.
        eq_a = Text("x  ←  x + v(x, ", color=C_TEXT, font_size=32, weight=BOLD, t2c={"v(x, ": C_CLEAN})
        eq_b = Text(") · Δτ", color=C_CLEAN, font_size=32, weight=BOLD)
        tau_ph = Text("0.00", color=C_CLEAN, font_size=32, weight=BOLD)  # reserves width for the live τ
        eqrow = VGroup(eq_a, tau_ph, eq_b).arrange(RIGHT, buff=0.06)
        ann = Text("τ = current timestep;   Δτ = step size;   v = the model's predicted nudge",
                   color=C_MUTED, font_size=22)
        VGroup(eqrow, ann).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=0.35)
        tau_center = tau_ph.get_center()
        eqrow.remove(tau_ph)
        eq_tau = always_redraw(lambda: Text(f"{lvl():.2f}", color=C_CLEAN, font_size=32, weight=BOLD).move_to(tau_center))
        self.play(Write(eq_a), Write(eq_b), FadeIn(eq_tau), FadeIn(ann))

        # each descent applies one Euler step; τ ticks down live with the dot
        for level in [0.7, 0.4, 0.15, 0.0]:
            arrow = Arrow(dot.get_center(), pos(level), color=C_CLEAN, buff=0.1, stroke_width=4, max_tip_length_to_length_ratio=0.2)
            vlab = Text("v", color=C_CLEAN, font_size=26, slant=ITALIC).next_to(arrow, RIGHT, buff=0.12)
            self.play(GrowArrow(arrow), FadeIn(vlab), run_time=0.4)
            self.play(dot.animate.move_to(pos(level)), FadeOut(arrow), FadeOut(vlab), run_time=0.9)
        self.play(dot.animate.set_color(C_CLEAN))
        self.wait(1.2)
