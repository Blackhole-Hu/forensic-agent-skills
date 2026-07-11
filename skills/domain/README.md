# Domain Forensics Skills

Domain-specific forensic skills covering network analysis, disk forensics, steganography, cryptography, reverse engineering, mobile forensics, cross-evidence correlation, vehicle forensics, AI-assisted workflows, and competition optimization.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `network-forensics/` | PCAP analysis, TLS decryption, covert channels, webshell traffic | Draft |
| `disk-forensics/` | Disk image analysis, filesystem forensics, deleted file recovery | Draft |
| `stego/` | Image/audio/video/document steganography detection and extraction | Draft |
| `crypto/` | Encoding identification, hash cracking, RSA attacks, password recovery | Draft |
| `reverse-engineering/` | Binary disassembly, unpacking, algorithm reversing | Draft |
| `android-analysis/` | APK reverse engineering, mobile forensics, native library analysis | Draft |
| `cross-evidence/` | Multi-source correlation, credential chains, data propagation | Draft |
| `vehicle-forensics/` | CAN bus, ECU firmware, T-BOX telematics, EDR data | Draft |
| `ai-forensics-workflow/` | AI-assisted analysis with MCP plugins | Draft |
| `optimization-strategy/` | Competition strategies for large-file scenarios | Draft |

## Relationship to Core

Domain skills are invoked by `forensic-router` after `file-triage` classifies the material. The router reads `triage_notes` and dispatches to the appropriate domain skill (e.g., PCAP → `network-forensics`, E01 → `disk-forensics`, APK → `android-analysis`).

## Migration Source

10 domain skills that had no equivalent in the original repo structure. Migrated and adapted from competition practice.
