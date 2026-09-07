# FactoryLens Pre-Launch Playbook

This document turns the waiting period before field hardware arrives into a public launch runway.

FactoryLens is currently software-complete for the v0.1 story, but the real CNC field-validation gates remain open. Public communication must keep that distinction explicit.

## 1. Hardware-free 45-second demo

Run:

```bash
python -m pip install -e ".[dev]"
python examples/prelaunch_demo.py --realtime --duration 45
```

Fast preview without waiting:

```bash
python examples/prelaunch_demo.py
```

The demo prints a clearly marked simulated timeline and writes:

```text
data/prelaunch-demo/
├── timeline.jsonl
└── manifest.json
```

Suggested screen-recording sequence:

1. show the repository title for 2 seconds;
2. run the realtime demo in a large terminal;
3. keep `SIMULATION ONLY` visible at the top;
4. open `manifest.json` at the end;
5. finish on the README field-prototype image and repository URL.

Recommended caption:

> FactoryLens pre-launch simulation. The machine RUN/STOP signal and evidence media are simulated until the first camera and CNC field-validation run is completed.

## 2. Social preview

Source artwork: [`docs/assets/social-preview.svg`](assets/social-preview.svg)

Message hierarchy:

- FactoryLens
- Observability for machines that don't have APIs.
- Camera • Voice • Machine Signals • Evidence
- Open Source / Pre-Alpha

GitHub's repository social-preview setting requires a raster image upload in the repository settings UI. Export the SVG to PNG at 1200 × 630 and upload it under **Settings → General → Social preview**.

## 3. Discovery topics

Recommended repository topics:

```text
cnc
manufacturing
industrial-iot
computer-vision
edge-ai
machine-monitoring
rtsp
opencv
python
modbus
opc-ua
industry-40
machine-vision
open-source
predictive-maintenance
```

Use the strongest 10–15 topics rather than stuffing unrelated keywords. GitHub topics currently require repository-settings access that is not exposed through the connected automation interface, so they must be added once in the GitHub UI.

## 4. Creator profile

A copy-ready profile README is in [`docs/PROFILE_README.md`](PROFILE_README.md).

To activate it, create a public repository named exactly `aaariel18/aaariel18`, place the draft at its root as `README.md`, then pin `factorylens` on the GitHub profile. Repository creation and profile pinning are account-level UI actions and are not exposed through the current connector.

## 5. Build in public

Do not post only release announcements. Publish the problem, decisions, failures, and field evidence.

Suggested sequence before the camera arrives:

| Post | Story | Proof |
| --- | --- | --- |
| 1 | Why legacy machines are hard to observe | architecture diagram + problem statement |
| 2 | Human-to-machine metadata | three-finger → voice → material/process flow |
| 3 | Why ambiguity must fail closed | S45C/SUS304 ambiguity example |
| 4 | Black-box evidence design | pre-roll + 0/+2/+10 snapshots + manifest |
| 5 | Hardware-free pre-launch demo | 45-second simulated terminal recording |
| 6 | What is still *not* validated | field-validation checklist |
| 7 | Camera arrival | unboxing/setup, no inflated claims |
| 8 | First real CNC cycle | metrics, failures, evidence bundle, lessons learned |

A good rhythm is one substantial technical post every 4–7 days, with shorter progress notes between them.

## 6. Community launch plan

Use platform-specific framing rather than pasting one promotional paragraph everywhere.

Primary targets:

- LinkedIn: manufacturing, automation, edge AI, computer vision, Python;
- Hacker News: `Show HN` after the simulated demo is polished and the README is easy to run;
- Reddit: relevant CNC, Python, computer-vision, self-hosted, open-source, and industrial-automation communities, subject to each community's self-promotion rules;
- DEV / Hashnode: technical build article explaining the architecture and why the project exists;
- X / Bluesky / Mastodon: short clips, screenshots, milestone updates, and links to deeper writeups;
- Discord/Slack communities: only where project sharing is explicitly allowed.

Do not mass-post the same copy. Lead with the problem, demonstrate the project, and disclose the current pre-alpha / field-validation state.

Ready-to-post copy is in [`docs/LAUNCH_POSTS.md`](LAUNCH_POSTS.md).

## 7. Contributor funnel

The repository should always have small, bounded work that a newcomer can complete without access to a CNC.

Good first issues should have:

- a one-paragraph problem statement;
- file/module hints;
- a small acceptance checklist;
- tests or docs expectations;
- no dependence on private factory credentials or production footage.

Initial contributor-friendly issues are tracked directly in GitHub and should stay intentionally small.

## 8. Ethical growth and traffic measurement

Never buy stars, followers, clones, comments, or fake traffic. They distort every useful signal and make maintainer decisions worse.

Track conversion instead:

```text
referral → unique visitor → README engagement → clone → star → issue/discussion → contributor
```

Review **Insights → Traffic** after every major promotion. Log at least:

- unique visitors;
- total views;
- unique cloners;
- top referring sites;
- stars gained in the same period;
- new issues/discussions;
- first-time contributors.

A small audience that files useful issues is more valuable than a large silent audience.

## Pre-launch exit criteria

Before calling the marketing runway ready:

- [x] software-side v0.1 workflow is merged;
- [x] 45-second hardware-free demo exists;
- [x] social-preview artwork exists;
- [x] creator-profile copy exists;
- [x] build-in-public editorial calendar exists;
- [x] launch copy exists for major channels;
- [x] contributor-friendly issues exist;
- [x] ethical growth / traffic measurement rules are documented;
- [ ] GitHub topics are added in repository settings;
- [ ] repository social-preview PNG is uploaded in settings;
- [ ] `aaariel18/aaariel18` profile repository is created and profile README copied;
- [ ] FactoryLens is pinned on the GitHub profile;
- [ ] external posts are published by the maintainer on the chosen accounts.

The last five items require account-level or third-party UI access that is not available to the repository connector.
