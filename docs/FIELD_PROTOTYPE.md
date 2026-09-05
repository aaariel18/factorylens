# CNC Field Prototype

These field notes document the first physical camera-placement experiments for FactoryLens on a CNC milling machine.

![Annotated CNC field prototype](assets/factorylens-field-prototype.jpg)

The goal is not to claim a production-ready installation. The goal is to record what was tested, what the camera can see, and what must be improved before reliable event capture and computer vision are attempted.

## Photo 1: initial camera positioning

The camera is being positioned beside the spindle area using a fabricated metal bracket. This stage is useful for checking field of view, mechanical clearance, cable direction and whether the camera can observe the intended spindle/tool region without obstructing machine movement.

## Photo 2: mounted close observation angle

The camera is fixed to the bracket and aimed toward the spindle area. This is the type of view that can later support a small ROI for tool-presence or machine-state observation. The bracket should be checked for vibration, fastener loosening and collision clearance during all machine motions.

## Photo 3: observation during machining setup

The camera has a wider operational view that includes the spindle, tool and workpiece/fixture area. This placement is valuable for event evidence because one frame can provide context around the machining cycle instead of showing only an isolated tool tip.

## Photo 4: first field deployment milestone

The CNC machine and operator environment are shown together after the initial installation work. This marks the transition from a software-only prototype toward a real machine-observability experiment.

## What these photos tell us

The physical prototype already answers several important design questions:

1. A camera can be mounted close enough to observe the spindle/work area without relying on a distant room-level CCTV view.
2. A dedicated bracket is practical, but vibration, collision envelope and cable strain relief must be treated as engineering requirements.
3. The view can include both a narrow tool ROI and enough surrounding context for evidence recording.
4. Chips, coolant, oil mist, reflections and changing machine lighting are real deployment conditions and must be represented in future datasets and tests.
5. The camera location is close enough that microphone quality should be tested carefully before relying on camera audio for operator voice notes.

## Next field validation checklist

Before calling the mounting production-ready, validate:

- full X/Y/Z machine travel and tool-change clearance;
- camera/bracket vibration at idle, spindle run and cutting conditions;
- cable strain relief and routing outside moving/abrasive zones;
- lens protection from chips, coolant and oil while keeping the microphone path usable;
- exposure and glare with machine lights on/off and wet surfaces;
- RTSP stability for a complete machining cycle;
- actual frame rate and reconnect behavior;
- ROI stability after vibration and repeated machine cycles;
- audio intelligibility with spindle, coolant and nearby machines running.

## Safety boundary

FactoryLens is an observation and evidence system. Camera placement must not interfere with guarding, interlocks, emergency-stop access, machine travel or certified safety systems. Computer-vision output must not be used as a substitute for safety-rated machine controls.
