# CNC Field Prototype

These field notes document the first physical FactoryLens camera installation on a CNC milling machine.

![Annotated CNC field prototype](assets/factorylens-field-prototype.jpg)

The first camera installation is now complete. This does **not** mean the system is production-ready or field-validated yet. The goal of this stage is to move from placement experiments into real validation of mounting, stream stability, image quality, audio, gesture input and cycle evidence capture.

## Photo 1: operator + installed CNC prototype

The operator and CNC environment are shown together after the first installation milestone. This is the clearest project-level proof that FactoryLens has moved beyond a software-only concept and into a real machine environment.

## Photo 2: camera positioning and bracket fit

The camera is positioned beside the spindle area using a fabricated metal bracket. This view is useful for checking field of view, mechanical clearance, cable direction and whether the camera can observe the intended spindle/tool region without obstructing machine movement.

## Photo 3: mounted close observation angle

The camera is fixed to the bracket and aimed toward the spindle area. This is the type of view that can later support a small ROI for tool-presence or machine-state observation. The bracket still needs vibration, fastener, collision-clearance and cable-strain checks during real machine motion.

## Photo 4: installed operational observation view

The installed camera has a wider operational view that includes the spindle, tool and workpiece/fixture area. This placement is valuable for event evidence because one frame can provide context around the machining cycle instead of showing only an isolated tool tip.

## Installation milestone

The first physical camera installation answers an important question: the proposed FactoryLens observation point is mechanically possible on the CNC prototype and can provide a useful view of the spindle/work area.

What remains open is validation under actual operation. A successful installation is not yet proof of reliable monitoring.

## What these photos tell us

1. A camera can be installed close enough to observe the spindle/work area without relying on distant room-level CCTV.
2. A dedicated bracket is practical, but vibration, collision envelope and cable strain relief remain engineering requirements.
3. The selected view can include both a narrow tool ROI and enough surrounding context for evidence recording.
4. Chips, coolant, oil mist, reflections and changing machine lighting are real deployment conditions and must be represented in future tests and datasets.
5. The camera location is close enough that microphone quality should be tested carefully before relying on camera audio for operator voice notes.
6. The project can now proceed from mounting work into RTSP, gesture, audio and complete-cycle field validation.

## Next field validation checklist

Before calling the installation field-ready, validate:

- full X/Y/Z machine travel and tool-change clearance;
- camera/bracket vibration at idle, spindle run and cutting conditions;
- fastener security after repeated machine cycles;
- cable strain relief and routing outside moving/abrasive zones;
- lens protection from chips, coolant and oil while keeping the microphone path usable;
- exposure and glare with machine lights on/off and wet surfaces;
- RTSP stability for a complete machining cycle;
- actual frame rate, latency and reconnect behavior;
- ROI stability after vibration and repeated machine cycles;
- gesture accuracy from the intended operator standing position;
- audio intelligibility with spindle, coolant and nearby machines running;
- one complete machine cycle that produces a reviewable evidence bundle.

## Safety boundary

FactoryLens is an observation and evidence system. Camera placement must not interfere with guarding, interlocks, emergency-stop access, machine travel or certified safety systems. Computer-vision output must not be used as a substitute for safety-rated machine controls.
