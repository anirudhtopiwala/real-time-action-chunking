"""Figure: handoff — chunk B is generated AHEAD of chunk A and reuses the overlap
as its committed prefix. B's steps (5..12) overlap A's committed tail (5..8)."""

from manim import *

from common import CELL, GAP, C_FROZEN, C_MUTED, C_NOISE, C_TEXT, step_cell, styled, title

PITCH = CELL + GAP


class Handoff(Scene):
    def construct(self):
        styled(self)
        head = title("Chunk B runs ahead of A — and reuses the overlap").scale(0.56).to_edge(UP, buff=0.5)
        self.play(FadeIn(head))

        N, OV = 8, 4  # chunk size, overlap (= H - s)
        span = N + OV
        x0 = -(span - 1) / 2 * PITCH
        def xpos(p):
            return x0 + p * PITCH

        # Chunk A (previous): labels 1..8 at columns 0..7; first 4 executed (blue), last 4 committed (green)
        aY = 1.25
        aCells = VGroup(*[
            step_cell("clean" if i < N - OV else "frozen", label=i + 1).move_to([xpos(i), aY, 0])
            for i in range(N)
        ])
        aLab = Text("chunk A · previous chunk", color=C_TEXT, font_size=24).next_to(aCells, UP, buff=0.3)
        self.play(FadeIn(aCells), FadeIn(aLab))
        self.wait(0.4)
        aTail = VGroup(*aCells[N - OV:])

        # Chunk B (next): labels 5..12 at columns 4..11; first 4 prefix (green), last 4 postfix (amber)
        bY = -1.35
        bCells = VGroup(*[
            step_cell("frozen" if i < OV else "noise", label=i + 5).move_to([xpos(i + OV), bY, 0])
            for i in range(N)
        ])
        bLab = Text("chunk B · next chunk, ahead in time", color=C_TEXT, font_size=24).next_to(bCells, UP, buff=0.3)
        bPrefix = VGroup(*bCells[:OV])
        bPost = VGroup(*bCells[OV:])

        # committed overlap slides straight down from A's tail into B's prefix (same columns)
        self.play(TransformFromCopy(aTail, bPrefix), run_time=1.2)
        self.play(FadeIn(bPost), FadeIn(bLab))

        guides = VGroup(*[
            DashedLine([xpos(N - OV + i), aY - CELL / 2, 0], [xpos(N - OV + i), bY + CELL / 2, 0],
                       color=C_MUTED, stroke_width=1).set_opacity(0.35)
            for i in range(OV)
        ])
        self.play(FadeIn(guides))

        br1 = Brace(bPrefix, DOWN, color=C_FROZEN)
        t1 = Text("committed prefix · from A", color=C_FROZEN, font_size=21).next_to(br1, DOWN, buff=0.12)
        br2 = Brace(bPost, DOWN, color=C_NOISE)
        t2 = Text("freshly generated", color=C_NOISE, font_size=21).next_to(br2, DOWN, buff=0.12)
        self.play(FadeIn(br1), FadeIn(t1), FadeIn(br2), FadeIn(t2))
        self.wait(1.5)
