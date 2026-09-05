# Contributing to FactoryLens

FactoryLens is an early project. Clear field reports and small, testable improvements are more valuable than giant pull requests.

## Good contributions

- document a real machine-integration problem;
- improve the Open Machine Event schema;
- add a small RTSP, Modbus, OPC UA, MQTT, or sensor adapter;
- improve test coverage;
- add reproducible benchmark notes;
- improve onboarding for people new to industrial computer vision.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
ruff check .
```

## Pull requests

1. Open or reference an issue for substantial changes.
2. Keep one concern per pull request.
3. Add tests for behavior changes.
4. Do not commit factory credentials, private production media, or proprietary machine programs.
5. Explain how you tested the change.

## Machine data and media

Only contribute data that you have the right to publish. Remove operator faces, badges, production orders, customer parts, serial numbers, IP addresses, credentials, and other sensitive information unless publication is intentional and authorized.

## Safety boundary

FactoryLens is an observability project. Contributions that directly control hazardous motion, bypass safety interlocks, or present the software as a certified safety system are out of scope.
