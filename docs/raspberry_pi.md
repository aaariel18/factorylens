# Raspberry Pi Deployment

FactoryLens can be deployed on a Raspberry Pi-class edge device for lightweight and local machine observability workloads.

This guide focuses on the light dependency FactoryLens components and provides a practical Linux deployment path for edge hardware.

> **Testing status:**
> The commands in this guide follow the documented FactoryLens Python and Linux setup.
> Raspberry Pi-specific hardware performance has not been validated as part of this guide.
> Test the selected workload on the target device before relying on it for field deployment.

## Expected environment

FactoryLens needs Python 3.11 or new versions.

Before installing FactoryLens, verify the Python version on the device:

```bash
python3 --version
```

The project currently declares Python 3.11+ as its requirement.
The repository specifically lists Python 3.11 and 3.12 in its classifiers

If the installed Python version is older than the 3.11, install a supported Python version using the package management method suitable for the Raspberry Pi version in use.

## Create a virtual environment

Create an virtual environment for Factorylens rather than installing its dependencies into the system.
Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

From a local checkout of FactoryLens, install the core package:

```bash
python -m pip install -e .
```

For camera support, install the optional camera dependency,

```bash
python -m pip install -e ".[camera]"
```

For development and testing,

```bash
python -m pip install -e ".[dev]"
```

Additional optional components can be installed when they are needed:

```bash
python -m pip install -e ".[gesture]"
python -m pip install -e ".[speech]"
```

The optional components are intentionally kept separate. A low-power edge device does not need to install every FactoryLens dependency

For example, an RTSP camera deployment can use

```bash
python -m pip install -e ".[camera]"
```

while an audio deployment using the FactoryLens speech or audio components may also require the optional dependencies.

## RTSP camera networking

FactoryLens uses RTSP sources for camera input. The camera and Raspberry Pi should be able to communicate over the local network.

Before troubleshooting FactoryLens itself, verify this,

- the Raspberry Pi can reach the camera's network address.
- RTSP port is reachable
- the selected RTSP stream is enabled on the camera.
- the camera is on a network path that provides enough bandwidth.
- firewall rules permit the required traffic.

Keep RTSP credentials outside the repository. FactoryLens supports the `FACTORYLENS_RTSP_URL` environment variable:

```bash
export FACTORYLENS_RTSP_URL='rtsp://USERNAME:PASSWORD@CAMERA_IP:554/stream1'
```

Don't commit the real value to Git.

For a persistent deployment, store the value in an env file rather than putting these credentials directly into a service definition

```bash
sudo mkdir -p /etc/factorylens
sudo nano /etc/factorylens/factorylens.env
```

Eg:

```text
FACTORYLENS_RTSP_URL=rtsp://USERNAME:PASSWORD@CAMERA_IP:554/stream1
```

Protect the file

```bash
sudo chmod 600 /etc/factorylens/factorylens.env
```

FactoryLens redacts RTSP credentials when source URIs are used as metadata or logging context.
Don't disable this protection or add the credentials to debug an output.

### Stream selection

Cameras that expose multiple RTSP streams can provide a high quality stream and lower bandwidth stream.

Use the high quality stream when the workload needs additional visual detail and the device and network can sustain the details.
A low bandwidth stream may be better for connectivity tests or CPU constrained multi camera deployments.

Benchmark the actual camera and network instead of relying on nominal FPS.
FactoryLens exposes reported capture FPS and measured processing FPS so that the callers can observe the difference.

### RTSP validation

The FactoryLens RTSP adapter provides a field-validation command,

```bash
factorylens validate-rtsp \
  --source-id cnc-03-spindle \
  --duration 60 \
  --snapshot data/validation/cnc-03-first-frame.jpg \
  --report data/validation/cnc-03-rtsp-report.json
```

The command reads `FACTORYLENS_RTSP_URL` by default.

A useful validation sequence is

1. Validate the stream while the machine is idle for 60 seconds.
2. Validate during a complete machining cycle.
3. Interrupt the camera or network path and observe reconnect behavior
4. Compare reported FPS, measured FPS and observed read FPS
5. Inspect the saved frame for the region of interest.
6. Check for vibration-induced view drift, glare, coolant obscuration and cable movement
7. Repeat with a low bandwidth stream if the target device cannot sustain the primary stream

Generated validation reports should remain under `data/`.
The repository ignores this directory so that production imagery and machine details aren't accidentally published

## FFmpeg

FFmpeg is required when using FactoryLens functionality that captures audio through the FFmpeg based RTSP audio adapter.

Install FFmpeg using the package manager provided by the Raspberry PI installation

```bash
sudo apt update
sudo apt install ffmpeg
```

Verify the installation :

```bash
ffmpeg -version
```

The FactoryLens audio capture path limits a operator note recording to a maximum duration and can stop after confirmed silence.
The default maximum duration is 120 seconds.

If audio capture is not being used, FFmpeg is not required solely for the RTSP video adapter.

## Storage layout

Keep generated runtime data separate from the source checkout whenever it's possible.

FactoryLens documentation uses the `data/` directory for generated validation reports, snapshots and other local runtime artifacts.
For example:

```text
factorylens/
├── data/
│   └── validation/
│       ├── *.jpg
│       └── *.json
├── docs/
├── examples/
├── src/
└── tests/
```

Do not commit production camera images, audio recordings, machine credentials or other sensitive machine data into Git.

For a long-running edge installation, monitor the available disk space.
Evidence recordings and media files can consume storage much faster than the source code or JSON metadata.

If systemd is used, service output could be inspected through the systemd journal

```bash
journalctl -u factorylens-validate.service
```

Follow service log when trouble shooting:

```bash
journalctl -u factorylens-validate.service -f
```

## Low power hardware expectations

A Raspberry Pi-class device should be treated as an edge computer with limited CPU, memory, storage and thermal headroom.
In particular, do not assume that one low-power device can efficiently run

- heavy multi-camera inference,
- high resolution video processing across many streams,
- multiple CPU intensive vision models at full frame rate,
- speech-to-text workloads at desktop class throughput and
- every optional FactoryLens component at the same time.

Start with one lightweight workload and measure CPU & memory usage, temperature, storage growth, network traffic and observed processing FPS.

If the workload cannot sustain the required rate, reduce stream resolution or bandwidth, can also reduce the no of simultaneous streams or move CPU intensive processing to a more capable edge/host system.

The RTSP source adapter is responsible for capture and timing.
Detection, gesture recognition, machine-state inference, speech processing and video evidence recording are separate components and should be evaluated independently.

## Running FactoryLens with systemd

For unattended Linux deployments, systemd can be used to manage FactoryLens' processes and collect the output in its journal.

The exact service command should match the FactoryLens workload being deployed.
The example below runs the finite RTSP validation command as a managed service.

Create

```bash
sudo nano /etc/systemd/system/factorylens-validate.service
```

Use:

```ini
[Unit]
Description=FactoryLens RTSP validation
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=factorylens
WorkingDirectory=/opt/factorylens
EnvironmentFile=/etc/factorylens/factorylens.env
ExecStart=/opt/factorylens/.venv/bin/factorylens validate-rtsp --source-id cnc-03-spindle --duration 60 --snapshot data/validation/cnc-03-first-frame.jpg --report data/validation/cnc-03-rtsp-report.json

[Install]
WantedBy=multi-user.target
```

The paths and service user in this are some deployment choices, not requirements of Factorylens.
Create the corresponding user, directory and venv environment according to the local deployment layout.

Reload systemd after creating or changing the service:

```bash
sudo systemctl daemon-reload
```

Manually run the validation service .

```bash
sudo systemctl start factorylens-validate.service
```

Check its status:

```bash
sudo systemctl status factorylens-validate.service
```

View its output,

```bash
journalctl -u factorylens-validate.service
```

This validation command is finite and therefore uses `Type=oneshot`.
A continuous FactoryLens workload should use a service definition matching the actual long-running command provided by that workload rather than turning the finite validation command into an artificial daemon.

## Security and operational notes

- Keep camera credentials in env files or any protected mechanism.
- Do not commit `.env` files containing real credentials.
- Do not publish private production media or machine information.
- Protect recorded evidence and local storage according to the deployment's access requirements.
- Monitor disk usage on devices that retain evidences locally.
- Use safe cable routing and suitable physical mounting for cameras and edge devices.
- FactoryLens is an observability system, not a safety controller.
  Camera status, vision output or FactoryLens state must never replace certified machine guarding, safety interlocks, emergency stops or safety PLC logic.

The guide does not establish

- a supported Raspberry Pi model matrix,
- guaranteed FPS or latency,
- guaranteed multi-camera capacity,
- production suitability of heavy inference workloads and
- replacement of certified industrial safety systems.

Validate the complete workload on the target hardware, camera, network and operating environment before using it in an actual machine deployment.
