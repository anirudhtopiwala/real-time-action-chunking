# Action Conditioning: Why Robots Stutter (and How to Make Them Flow)

*Smooth real-time chunking for robot policies (VLAs).*

## The problem nobody warns you about

Train a policy to control a robot and you learn quickly that predicting one action at a time doesn't work. It's slow, and it's twitchy, small errors pile up until the arm wanders into states it never saw in training. So most modern manipulation policies (VLAs, or Vision-Language-Action models) predict an **action chunk** instead: a short burst of future actions, maybe half a second to a couple of seconds' worth, generated all at once. The robot runs part of the chunk, then asks for the next one.

This works beautifully, right up until you watch the handoff from one chunk to the next.

Each chunk is generated more or less on its own. One ends with the gripper drifting left; the next, computed a fraction of a second later, has a slightly different idea of where the gripper should be, and the robot snaps between them. These policies sample their actions too, so two chunks can disagree even from the exact same observation. The result is a stutter at every boundary, an out-of-distribution "jerk" that shows up as visible judder, and in the worst case as instability that throws the task off the rails.

![Two consecutive action chunks with a jerk at the boundary, then the smooth version](assets/the-seam.gif)

## The real-time twist: you can't avoid the seam

The frustrating part is that you can't engineer this away. Generating a chunk takes time, the inference delay, and the robot can't freeze while it waits; it keeps executing actions from the current chunk. By the time the new chunk is ready, the robot has already committed to its first few steps.

So handing off mid-motion isn't a choice, the timing forces it. Some prefix of the new chunk is already being executed by the time the chunk arrives, and if the fresh chunk disagrees with those actions, that's your jerk.

The fix falls out of the problem. Don't let the new chunk start from scratch. Condition it on the actions you've already committed to, treat that committed prefix as fixed, and let the policy invent only what comes after.

![Chunk B runs ahead of A and reuses the committed overlap as its fixed prefix](assets/handoff.gif)

That idea, conditioning a chunk on a prefix of already-decided actions, is **action conditioning**, and it's the core of **real-time chunking (RTC)**. The interesting question is where you do it, during training or at inference.

## A 30-second primer: how a chunk gets generated

Most chunking policies generate actions by diffusion, or flow-matching. You start from pure noise and denoise it into a clean action over a handful of steps.

Picture each action as a point on a line between noise and clean. The flow-matching timestep is just how far along that line you are, pure noise at one end, the finished action at the other. Generation starts at the noise end and walks toward clean, integrating the model's predicted velocity at each step to nudge the action along.

![A step integrated from Gaussian noise to a clean action, with the Euler update and a live timestep](assets/denoise-primer.gif)

## The mechanism: fix the prefix, denoise the rest

Conditioning is simpler than it sounds. For the committed prefix, you do two things. First, set its content to the **ground-truth committed actions**, not noise. Second, set its **timestep to the clean end**, marking it as fully denoised.

The rest of the chunk, the postfix, is left to denoise as usual. The prefix effectively tells the model "these are already clean and known, build around them," and the model spends its effort only on the postfix.

Content and timestep have to agree, though. Clean content wearing a noisy timestep is a mixed signal, and the timestep is a genuine input, the model reads a "how noisy am I?" value for every token. So the one thing conditioning asks of the architecture is a per-token timestep, clean on the prefix and noisy on the postfix. Get that right and the conditioning stays stable across the whole denoising loop.

![The per-token timestep as a noise-level input: the prefix pinned clean, the postfix noisy](assets/timestep-signal.gif)

## How much to condition on?

How big should the prefix be? Anywhere from a light touch to a firm grip.

The lightest option is to pin only the one next committed action. It tacks the new chunk to a single point and leaves everything else free, cheap continuity, but weak, since the plan can drift away right after that point.

![Condition on one committed step; the trajectory meets at a point, then diverges](assets/single-action.gif)

A firmer option is to pin the whole set of committed actions, every step the robot will have executed by the time the chunk lands. Now the two chunks have to agree over a whole stretch rather than a single point, and the handoff comes out smooth. This is the version the paper we're discussing uses.

![Freeze the whole committed prefix; the trajectory matches across the overlap, then parts ways](assets/full-prefix.gif)

## How long is the prefix? It's the inference delay

You don't actually pick the prefix length; the inference delay picks it for you. Call the delay `d`, the number of control steps that pass while the model computes the next chunk. If generation starts at step `t` and the chunk lands at `t + d`, the robot has executed `d` actions in the meantime, and those `d` actions are the prefix. **The delay and the number of conditioned steps are the same number.**

There's a ceiling, of course. The prefix can only reuse actions where the old and new chunk overlap, which gives `d ≤ H − s` (prediction horizon minus execution horizon). Push `d` past that and there's nothing left to condition on.

![Sweeping the inference delay d; the committed prefix grows and shrinks, bounded by d ≤ H − s](assets/action-delay.gif)

In practice you don't hardcode one `d`, since real-world latency wanders from run to run. You train over a range of delays instead, sampling `d` each step so a single checkpoint copes with whatever latency it meets (the paper samples uniformly from 0 to 10, about 200 ms on a 50 Hz robot). Bigger `d` is also where this approach pulls ahead, because the older inference-time method has to work harder to stay consistent as the prefix grows.

## Where does the conditioning happen?

The paper, "Training-Time Action Conditioning for Efficient Real-Time Chunking," does the conditioning during training. PI's earlier work did it at inference. Same target, opposite ends.

One route is to condition at **inference time**. Take an already-trained model and steer it toward the prefix as it samples, with an inpainting-style guidance step (pseudoinverse guidance). It's flexible, but it isn't free, the guidance needs an extra backward pass on every denoising step, which piles latency onto a system whose whole point is speed.

The other route conditions at **training time**. You simulate the delay while training, marking a prefix of each chunk as committed, feeding it in as clean conditioning (ground-truth content, clean timestep), and training the model to denoise the rest around it. The model just learns to condition on prefixes. At deployment there's nothing extra to run, no guidance and no inpainting, so no added latency.

And it holds up. In simulation, training-time conditioning beats the inference-time version at higher delays, and on real tasks (box building and espresso-making with the π0.6 VLA) it matches the task success and the speed of inference-time RTC while costing less to run. A practical drop-in replacement for inference-time inpainting.

There's also a parallel line of work (VLASH) that comes at the same seam from the other side, offsetting the state instead of the actions. Rather than freezing the committed actions, it rolls the robot's state forward, where the arm will be at execution time is just its current state plus the actions already committed, and conditions the policy on that predicted future state, leaving the (stale) camera image as-is. The new chunk then has no constraint on its actions at all; the policy generates whatever it likes, just from a corrected starting point. Fix the input rather than pin the output. The snag is the controller: if tracking error is large, the rolled-forward pose is wrong, and getting it right would mean running the controller's forward dynamics during the rollout, which hands the latency right back.

## The short version

- Action chunking is fast and stable but jerks at the boundaries, and in real time that seam is unavoidable, the robot has already committed to part of the next chunk before it's even generated.
- The fix is action conditioning: hold the committed prefix fixed (committed actions, clean timestep) and let the policy denoise the rest.
- You can pin one action (light) or the whole prefix (firmer and smoother), and you can do it at inference time (guidance, flexible but slower) or at training time (simulate the delay, nothing extra at deploy).
- **Training-time conditioning comes out ahead.** It's "make training look like deployment" applied directly: the model learns the exact prefix pattern it will meet at runtime and pays nothing extra there.

Tested these and seen it differently? Please comment.

---

## Credits

Based on "Training-Time Action Conditioning for Efficient Real-Time Chunking" ([arXiv:2512.05964](https://arxiv.org/abs/2512.05964)), which builds on Real-Time Chunking (RTC) from Physical Intelligence. The state-offset alternative is VLASH ([arXiv:2512.01031](https://arxiv.org/abs/2512.01031)). All research credit belongs to those authors.

All figures are original animations built with [Manim Community Edition](https://www.manim.community/) (originally created by Grant Sanderson / 3Blue1Brown). By Anirudh Topiwala.

## Reproducing the figures

```bash
pip install -r requirements.txt          # Manim; also needs ffmpeg on PATH
cd animations && ./render_all.sh         # render MP4s -> animations/media/videos/
../scripts/make_gifs.sh                  # MP4s -> optimized GIFs in assets/
```

Each animation is one self-contained Manim scene in `animations/` (e.g. `action_delay.py`), sharing style helpers from `animations/common.py`.

## License

Released under the [MIT License](LICENSE).
