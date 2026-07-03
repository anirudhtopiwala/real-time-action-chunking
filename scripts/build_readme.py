#!/usr/bin/env python3
"""Generate README.md from article.md: swap `<Figure: handle>` markers for the
inline GIFs in assets/, then append repo footer (reproduce / credits / license)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG_RE = re.compile(r"^>\s*\*\*`<Figure:\s*([a-z0-9\-]+)>`\*\*.*$", re.M)

FOOTER = """

---

## Reproducing the figures

```bash
pip install -r requirements.txt          # Manim; also needs ffmpeg on PATH
cd animations && ./render_all.sh         # render MP4s -> animations/media/videos/
../scripts/make_gifs.sh                  # MP4s -> optimized GIFs in assets/
python ../scripts/build_readme.py        # regenerate this README from article.md
```

Each animation is one self-contained Manim scene in `animations/` (e.g.
`action_delay.py`), sharing style/helpers from `animations/common.py`.

## Credits & attribution

This is an explanatory article + original animations. All research credit belongs
to the authors of the work described:

- **"Training-Time Action Conditioning for Efficient Real-Time Chunking"**, Kevin
  Black, Allen Z. Ren, Michael Equi, Sergey Levine (Physical Intelligence).
  [arXiv:2512.05964](https://arxiv.org/abs/2512.05964). The paper this article explains.
- **Real-Time Chunking (RTC)**, Physical Intelligence. The inference-time method
  it builds on.
- **"VLASH: Real-Time VLAs via Future-State-Aware Asynchronous Inference"** -
  Jiaming Tang, Yufei Sun, et al. (MIT / NVIDIA).
  [arXiv:2512.01031](https://arxiv.org/abs/2512.01031). The state-offset alternative discussed at the end.
- The `action-delay` animation re-creates Fig. 1 of the RTC paper, and
  `timestep-signal` echoes its Fig. 2; both are original redraws.
- **Animation engine:** all figures are made with
  [Manim Community Edition](https://www.manim.community/), the open-source
  math-animation engine originally created by Grant Sanderson (3Blue1Brown) and
  maintained by the Manim Community. Huge thanks to that project.

Article & animations by **Anirudh Topiwala**.

## License

Everything in this repository, code, article text, and figures, is released
under the [MIT License](LICENSE). Use it freely; please keep the attribution notice.
"""


def main() -> None:
    text = (ROOT / "article.md").read_text()
    text = FIG_RE.sub(lambda m: f"\n![{m.group(1)}](assets/{m.group(1)}.gif)\n", text)
    # drop the HTML placeholder comment if present
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S).rstrip()
    (ROOT / "README.md").write_text(text + FOOTER)
    print("wrote README.md")


if __name__ == "__main__":
    main()
