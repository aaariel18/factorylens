# Architecture

FactoryLens is designed as an event pipeline with replaceable adapters.

```text
Sources                    Interpretation              Core
────────────────────────────────────────────────────────────────
RTSP camera ───────────┐
microphone ────────────┤     gesture detector ─────┐
PLC / Modbus ──────────┼──>  state adapter ────────┼──> Event Bus
OPC UA ────────────────┤     speech parser ────────┤
GPIO / sensor ─────────┘     vision detector ──────┘
                                                      │
                                                      ▼
                                          Open Machine Events
                                                      │
                       ┌──────────────────────────────┼──────────────┐
                       ▼                              ▼              ▼
                  Evidence store                Local DB        Outputs
               video/audio/images              timeline       MQTT/webhook
```

## Core concepts

### Source
Produces raw observations: frames, audio, machine registers, digital inputs, or messages.

### Adapter / detector
Converts raw observations into a machine-relevant fact, such as a stable three-finger gesture, a Modbus RUN signal, a stack-light state, or a tool leaving a configured ROI.

### Event
A timestamped, machine-scoped record. Events are immutable facts, not mutable dashboard state.

### Evidence
A file or URI associated with an event: snapshot, video, audio, transcript, or other artifact.

### Session
A small state machine joining operator context to a machine cycle:

```text
IDLE → LISTENING → ARMED → RECORDING → COMPLETE
```

## Safety boundary

The core architecture is observation-oriented. FactoryLens should not silently become a motion-control layer. Any future write/control adapter must be explicit, isolated, and documented separately.

## Edge-first deployment

The preferred deployment keeps camera streams and production evidence local:

```text
machine network → edge PC → local storage
                         ↘ optional event metadata output
```
