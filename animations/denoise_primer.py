"""Figure: denoise-primer. A step is integrated from Gaussian noise (τ=0) to a
clean action (τ=1) by an Euler step xₜ₊₁ = xₜ + v(xₜ, τ)·Δτ, with τ shown live."""

from manim import *

from common import C_CLEAN, C_MUTED, C_NOISE, C_TEXT, styled, title


def xsub(sub, size=32, color=C_TEXT):
    """Render x with a subscript (font-safe manual subscript, no LaTeX)."""
    base = Text("x", font_size=size, color=color, weight=BOLD)
    s = Text(sub, font_size=int(size * 0.6), color=color, weight=BOLD)
    s.next_to(base, RIGHT, buff=0.02).align_to(base, DOWN).shift(DOWN * 0.05)
    return VGroup(base, s)


class DenoisePrimer(Scene):
    def construct(self):
        styled(self)
        head = title("How a step gets denoised").scale(0.6).to_edge(UP, buff=0.5)
        self.play(FadeIn(head))

        top, bot = UP * 2.3, DOWN * 2.3
        axis = Line(top, bot, color=C_MUTED, stroke_width=3)
        noise_lab = Text("pure noise   x₀ ~ Gaussian   (τ = 0)", color=C_NOISE, font_size=24).next_to(top, RIGHT, buff=0.4)
        clean_lab = Text("clean action   (τ = 1)", color=C_CLEAN, font_size=24).next_to(bot, RIGHT, buff=0.4)
        self.play(Create(axis), FadeIn(noise_lab), FadeIn(clean_lab))

        # τ = 0 at the noise end (top), τ = 1 at the clean end (bottom)
        def pos(tau):
            return top + (bot - top) * tau

        dot = Dot(pos(0.0), color=C_NOISE, radius=0.16)
        tau = lambda: (top[1] - dot.get_center()[1]) / (top[1] - bot[1])
        readout = always_redraw(lambda: Text(f"τ = {tau():.2f}", color=C_TEXT, font_size=28).next_to(dot, LEFT, buff=0.4))
        self.play(FadeIn(dot), FadeIn(readout))

        # Euler update xₜ₊₁ = xₜ + v(xₜ, τ)·Δτ, with a live τ. Nudge term in accent.
        p = [
            xsub("t+1"), Text(" = ", font_size=32, color=C_TEXT, weight=BOLD),
            xsub("t"), Text(" + v(", font_size=32, color=C_CLEAN, weight=BOLD),
            xsub("t", color=C_CLEAN), Text(", ", font_size=32, color=C_CLEAN, weight=BOLD),
            Text("0.00", font_size=32, color=C_CLEAN, weight=BOLD),  # τ placeholder
            Text(") · Δτ", font_size=32, color=C_CLEAN, weight=BOLD),
        ]
        eqrow = VGroup(*p).arrange(RIGHT, buff=0.05)
        ann = Text("x₀ = initial Gaussian noise      τ = current timestep      Δτ = step size",
                   color=C_MUTED, font_size=22)
        VGroup(eqrow, ann).arrange(DOWN, buff=0.22).to_edge(DOWN, buff=0.35)
        tau_center = p[6].get_center()
        eqrow.remove(p[6])
        eq_tau = always_redraw(lambda: Text(f"{tau():.2f}", color=C_CLEAN, font_size=32, weight=BOLD).move_to(tau_center))
        self.play(Write(eqrow), FadeIn(eq_tau), FadeIn(ann))

        for t in [0.3, 0.6, 0.85, 1.0]:
            arrow = Arrow(dot.get_center(), pos(t), color=C_CLEAN, buff=0.1, stroke_width=4, max_tip_length_to_length_ratio=0.2)
            vlab = Text("v", color=C_CLEAN, font_size=26, slant=ITALIC).next_to(arrow, RIGHT, buff=0.12)
            self.play(GrowArrow(arrow), FadeIn(vlab), run_time=0.4)
            self.play(dot.animate.move_to(pos(t)), FadeOut(arrow), FadeOut(vlab), run_time=0.9)
        self.play(dot.animate.set_color(C_CLEAN))
        self.wait(1.2)
