# FactoryLens Launch Posts

These drafts are deliberately transparent about the current state: software pre-alpha is implemented, while real CNC field validation waits for hardware.

## LinkedIn — English

**Millions of industrial machines can manufacture precision parts, but many still cannot tell software what just happened.**

I am building **FactoryLens**, an open-source observability and black-box recording project for legacy industrial machines.

The first CNC workflow connects:

`3-finger operator trigger → voice note → material/process metadata → machine RUN/STOP → pre-roll video + snapshots → one job evidence timeline`

The software-side v0.1 flow is now implemented in Python with RTSP, offline-first speech processing, machine-cycle provenance, debounce logic, evidence manifests, tests, and CI.

The next step is physical field validation once the camera hardware arrives. Until then, the public demo clearly labels machine-state signals as simulated.

I am especially interested in feedback from people working with CNC, PLCs, machine vision, edge AI, industrial IoT, and older machines that were never designed for modern observability.

Repository: https://github.com/aaariel18/factorylens

#opensource #manufacturing #cnc #industrialiot #computervision #edgeai #python

## LinkedIn — Indonesia

**Banyak mesin industri bisa membuat komponen presisi, tetapi tidak bisa menjelaskan ke software apa yang baru saja terjadi.**

Saya sedang membangun **FactoryLens**, proyek open-source untuk observability dan black-box recording pada mesin industri lama.

Workflow CNC pertamanya:

`trigger 3 jari → catatan suara operator → material/proses → RUN/STOP mesin → video pre-roll + snapshot → satu timeline evidence`

Alur software v0.1 sudah diimplementasikan dengan Python, RTSP, speech processing lokal, provenance sinyal mesin, debounce, evidence manifest, automated test, dan CI.

Validasi lapangan di CNC asli masih menunggu hardware kamera datang. Demo pre-launch sengaja menandai sinyal mesin sebagai **simulated**, jadi tidak ada klaim palsu seolah sudah field-tested.

Saya ingin belajar dari engineer/manufacturer yang bekerja dengan CNC, PLC, machine vision, edge AI, industrial IoT, atau mesin lama yang sulit diintegrasikan.

Repo: https://github.com/aaariel18/factorylens

## Hacker News — Show HN

**Title**

Show HN: FactoryLens – open-source observability for industrial machines without APIs

**Body**

I am building FactoryLens, an early-stage Python project for adding an event/evidence layer to legacy industrial machines.

The motivating problem is simple: a machine may run perfectly for 20 years while exposing almost no modern telemetry. Context ends up split between CCTV, operator notes, PLC signals, spreadsheets, and memory.

FactoryLens tries to turn those inputs into one timeline. The first CNC story is: operator gesture → voice note → normalized material/process metadata → machine cycle signal → pre-roll recording/snapshots → manifest.

The software path is implemented and tested, but physical CNC validation is still pending hardware arrival. The repository includes a hardware-free demo whose machine-state signal is explicitly marked simulated.

I would value criticism on the event model, machine-signal abstraction, evidence architecture, and what would make this useful outside my first CNC use case.

https://github.com/aaariel18/factorylens

## Reddit — technical / open-source communities

**Title**

I am building an open-source black-box recorder for legacy CNC machines — looking for architecture feedback

**Body**

I have been working on FactoryLens, a Python project that tries to make older industrial machines observable without assuming they have a modern API.

The current CNC workflow combines operator context and machine evidence:

- a 3-finger gesture can trigger an operator voice note;
- speech is normalized into material/process metadata;
- a machine RUN/STOP signal becomes a debounced cycle event with source provenance;
- cycle start can capture pre-roll video and snapshots;
- the job closes into an event/evidence manifest.

The software-side v0.1 is implemented, but the real CNC field-validation gates are still open because the ordered camera hardware has not arrived yet. There is a clearly marked simulation demo in the repo so people can inspect the flow without hardware.

I am not trying to treat camera inference as a safety signal, and the project is observation-only.

I would especially appreciate feedback from anyone who has integrated old CNC/PLC equipment, RTSP cameras, Modbus/OPC UA, machine vision, or shop-floor recording systems.

Repo: https://github.com/aaariel18/factorylens

Before posting, adapt the title/body to the specific subreddit and check its current self-promotion rules.

## DEV / Hashnode article outline

**Working title:**

Building FactoryLens: Observability for Machines That Don't Have APIs

**Opening:**

Modern software teams expect logs, traces, metrics, and event histories. Many industrial machines have none of those things. They may expose a few controller signals, sit under a CCTV camera, and depend on an operator to remember what material was loaded and what process was running.

FactoryLens started from a question: can we build a vendor-neutral observability layer around machines that were never designed to be observable?

**Sections:**

1. The legacy machine visibility problem
2. Why CCTV alone is not observability
3. Human-to-machine metadata: gesture + voice
4. Turning RUN/STOP into an event with provenance
5. Why debounce and measured/inferred distinctions matter
6. Pre-roll recording and evidence manifests
7. Safety boundary: observation is not machine control
8. The hardware-free simulation
9. What remains unvalidated
10. How contributors can help without owning a CNC

**Closing CTA:**

If you work with CNC, PLC, machine vision, edge systems, or industrial software, I would like FactoryLens to be shaped by real integration pain rather than assumptions. Issues and architecture feedback are welcome.

## Short post — X / Bluesky / Mastodon

Building **FactoryLens**: open-source observability for machines that don't have APIs. ⚙️

3-finger trigger → operator voice → material/process → machine cycle → pre-roll video + snapshots → evidence timeline.

Software v0.1 is implemented. Real CNC validation starts when the camera hardware arrives. The current demo is explicitly simulated.

https://github.com/aaariel18/factorylens

## Camera-arrival post

The camera for FactoryLens has arrived. Next milestone: stop simulating the machine-adjacent inputs and start measuring reality.

Field checklist:

- RTSP stability and reconnect behavior
- three-finger false positives
- microphone intelligibility with spindle/coolant noise
- speech-to-material/process accuracy
- real RUN/STOP signal mapping
- one complete CNC evidence bundle

I will publish the failures alongside the successes. That is the part that should make this project useful to other industrial integrations.

https://github.com/aaariel18/factorylens

## First-real-cycle post

Use this only after the field-validation evidence exists.

**FactoryLens just completed its first real CNC cycle.**

Replace this paragraph with measured results only: machine type, signal source, cycle duration, RTSP behavior, snapshot timing, CPU/RAM observations, dropped frames, speech accuracy, and known failures.

Do not publish production-sensitive footage, controller credentials, network details, operator audio, or customer data without explicit clearance.
