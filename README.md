# Why Robots Stutter, and the Fix Behind Real-Time Chunking

*Chunked policies jerk at the boundaries. "Action conditioning" smooths them, and a recent paper shows you can bake it in at training time for free.*

---

## The problem nobody warns you about

If you train a policy to control a robot, you learn fast that predicting one action at a time is a bad idea. It's slow, and it's twitchy. Small errors compound as the robot drifts into states it never saw in training. So most modern manipulation policies (VLAs included) predict an **action chunk**: a short burst of future actions, maybe a half-second to a couple of seconds' worth, all at once. The robot executes part of the chunk, then asks the policy for the next one.

This works beautifully, until you look closely at the moment one chunk hands off to the next.

Each chunk is generated more or less independently. The first chunk ends with the gripper drifting left. The next chunk, produced a fraction of a second later, has its own slightly different opinion about where the gripper should be. The robot snaps from one plan to the other. And because these policies *sample* their actions, two chunks can disagree even from the **exact same** observation. The result is a characteristic stutter at every boundary: an out-of-distribution "jerk" that shows up as visible judder and, at worst, instability that throws the task off the rails.


![the-seam](assets/the-seam.gif)


---

## The real-time twist: you can't avoid the seam

Here's what makes this unavoidable rather than a bug you can engineer away. Generating a chunk takes time. Call it the **inference delay**. While the model is busy computing the next chunk, the robot can't freeze; it keeps executing actions from the *current* chunk. So by the time the new chunk is ready, the robot has **already committed** to the first few of its steps.

You don't get to choose whether to hand off mid-motion. The real-time constraint forces it: some prefix of the new chunk corresponds to actions that are *already being executed*. If the fresh chunk disagrees with them, you get the jerk.

Which points straight at the fix: **don't let the new chunk start from scratch; condition it on the actions you've already committed to.** That committed prefix should be treated as fixed, and the policy should only get to invent what comes after.


![handoff](assets/handoff.gif)


This idea, conditioning a chunk on a prefix of already-decided actions, is **action conditioning**, and it's the heart of *real-time chunking (RTC)*. The rest of this post is about how you actually do it, and a neat recent result on where to do it.

---

## A 30-second primer: how a chunk gets generated

Most chunking policies generate actions by **diffusion / flow-matching**: start from pure noise and gradually "denoise" it into a clean action over a handful of steps.

Picture each action as a point on a line between *noise* and *clean*. A **flow-matching timestep** says how far along that line you are: one end is pure noise, the other is the finished, clean action. Generation starts at the noise end and walks to the clean end, and at each step the model predicts which way to nudge things toward clean.


![denoise-primer](assets/denoise-primer.gif)


---

## The mechanism: fix the prefix, denoise the rest

Conditioning turns out to be almost embarrassingly simple. For the committed prefix, do two things:

1. Set its **content** to the ground-truth committed actions (not noise).
2. Set its **timestep to the clean end**: mark it as fully denoised.

Leave the rest of the chunk (the *postfix*) alone: it stays noisy and denoises normally. That's it. The prefix is announced to the model as "already clean and known, attend to it," while the model spends its effort denoising only the postfix around it.

The catch is that the two have to agree. Clean *content* wearing a still-noisy *timestep* is a contradiction. And the timestep isn't bookkeeping; it's a real per-token "how noisy am I?" **input** the model reads for every token. So the one architectural tweak conditioning needs is to let that timestep **differ per token**: clean for the prefix, noisy for the postfix. That's what makes the conditioning honest and keeps it stable across the whole denoising loop.


![timestep-signal](assets/timestep-signal.gif)


---

## How *much* to condition on

There's a real design choice in how big a prefix you condition on, a spectrum from a light touch to a firm grip.

**A single action.** Condition on just the one next committed action, the minimal form. It tacks the new chunk to a single known point and lets everything else move freely. Cheap continuity, but weak: the plan can swing away right after that one point.


![single-action](assets/single-action.gif)


**A full prefix.** Condition on the *whole* set of committed actions, every step the robot will have executed by the time the chunk lands. Now the new chunk must agree with the old one over a whole stretch, not just a point, which makes for a genuinely smooth handoff. This is what the paper we're discussing does.


![full-prefix](assets/full-prefix.gif)


---

## How long is the prefix? It's the inference delay

The prefix length isn't a free hyperparameter; it's set by the **inference delay `d`**: how many control steps tick by while the model is computing the next chunk. If generation starts at step `t` and the chunk isn't ready until `t + d`, then by the time it lands the robot has already executed `d` actions. Exactly those `d` committed actions are the prefix. So **the delay and the number of steps you condition on are the same number.**

There's a hard limit: the prefix can only reuse actions where the old and new chunk *overlap*, which gives `d ≤ H − s` (prediction horizon minus execution horizon). Push `d` past that and there's nothing left to condition on.


![action-delay](assets/action-delay.gif)


And here's the practical bit: you don't hardcode one `d`, because real-world latency varies run to run. Instead you **train across a range of delays**: sample `d` each step so a single checkpoint is robust to whatever latency it meets at deployment (in the paper: uniform `0` to `10`, about 200 ms on a 50 Hz robot). Bigger `d` means a bigger prefix, and that's exactly where this approach pulls ahead, since the older inference-time method has to "work harder" to stay consistent as the prefix grows.

---

## Where the conditioning happens: the actual contribution

Here's the part the recent paper (*Training-Time Action Conditioning for Efficient Real-Time Chunking*, Physical Intelligence) is really about. You can inject this conditioning in two places.

**At inference time.** Condition the *already-trained* model on the prefix while it samples, using an inpainting-style guidance step (pseudoinverse guidance). This is flexible, but it isn't free: the guidance requires an extra backward computation *every denoising step*, which adds latency to a system whose entire premise is being fast.

**At training time.** Instead, **simulate the inference delay while training**: randomly mark a prefix of each chunk as "committed," feed it in as clean conditioning (content = ground truth, timestep = clean), and train the model to denoise the rest around it. The model *learns* to condition on prefixes directly. At deployment there's nothing extra to do: no guidance, no inpainting, no added latency. It's a few lines of code, no changes to the model architecture or the robot runtime.

And the payoff is real: in simulation, training-time conditioning **outperforms** the inference-time version at higher inference delays, and on real tasks (box building, espresso making with the π0.6 VLA) it matches both task performance and speed while being computationally cheaper. The one honest wrinkle: at the very lowest delays it's a hair behind (those earliest steps get slightly less training supervision), but that's the regime where the seam barely matters anyway. The takeaway the authors land on: **training-time action conditioning is a practical drop-in replacement for inference-time inpainting.**

**A different route: offset the state, not the actions.** There's a parallel line of work (e.g. VLASH) that attacks the same seam from the opposite side. Instead of freezing the committed *actions*, it rolls the robot's *state* forward (where the arm will be at execution time is just its current state plus the actions already committed) and conditions the policy on that future state, leaving the (stale) camera image as-is. Crucially, the new chunk is then predicted with **no constraint on its actions at all**: the policy is free to generate whatever chunk it wants, just from the corrected starting point. Same goal, opposite lever: fix the *input* state rather than pin the *output* actions. It's another perfectly good way to do this. (The two haven't been raced head-to-head: VLASH benchmarks against the older inference-time RTC, and the training-time RTC paper only name-checks VLASH, so there's no "which wins" verdict yet.)

### The three flavors, side by side

| Approach | Conditions on | Applied at | How | Extra cost at deploy |
|---|---|---|---|---|
| **Inference-time RTC** | committed actions (the prefix) | inference only | inpainting via pseudoinverse guidance during sampling | a backward pass on every denoising step |
| **Training-time RTC** | committed actions (the prefix) | training (simulate the delay) | fix the prefix as clean (timestep = clean), denoise the rest | none |
| **VLASH (state roll-forward)** | the robot's rolled-forward *state*, not the actions | training augmentation, then inference | roll the state forward by the committed actions, feed that future state in, leave the output actions free | none |

The split: the first two condition on the *actions* (constrain the output), VLASH conditions on the *state* (correct the input). And only inference-time RTC pays a per-step cost, the other two move the work into training and are free at runtime.

---

## The short version

- Action chunking is fast and stable but stutters at chunk boundaries, and in a real-time system the seam is *unavoidable*, because the robot has already committed to a prefix of the next chunk by the time it's generated.
- The cure is **action conditioning**: fix that committed prefix (content = the committed actions, flow timestep = clean) and let the policy denoise only the rest.
- You can condition on **a single action** (light) or **a full prefix** (firm and smooth).
- You can do it **at inference time** (inpainting/guidance, flexible but adds latency every step) or **at training time** (simulate the delay while training, free at deployment, and a drop-in replacement that matches or beats the inference-time version).
- The unifying idea: **make training look like deployment.** Simulate the real-time delay while you train, and the seam problem largely takes care of itself at runtime.

*Based on "Training-Time Action Conditioning for Efficient Real-Time Chunking" (Black, Ren, Equi, Levine, Physical Intelligence, arXiv:2512.05964), which builds on Real-Time Chunking (RTC).*

*All figures are original animations (built with Manim). Source + code: [github.com/anirudhtopiwala/real-time-action-chunking](https://github.com/anirudhtopiwala/real-time-action-chunking).*

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
