# Security Policy

FactoryLens may sit near cameras, machine networks, PLCs, and production records. Treat configuration and evidence as sensitive.

## Never commit

- `.env` files;
- RTSP / ONVIF usernames or passwords;
- PLC, OPC UA, MQTT, database, or API credentials;
- SSH keys, tokens, certificates, or private keys;
- private production video/audio;
- internal network inventories unless intentionally public.

Use `.env.example` and documentation placeholders instead.

## Reporting a vulnerability

Please avoid publishing exploitable details in a public issue when a vulnerability could expose credentials, production networks, or private media. Use GitHub's private security-reporting path if enabled, or contact the maintainer privately.

## Safety

A software vulnerability and a machine-safety hazard are not the same thing. FactoryLens must never be treated as a replacement for certified emergency stops, guards, interlocks, safety PLCs, or required machine-safety systems.
