---
name: vehicle-forensics
description: Connected vehicle and IoT forensics — CAN bus analysis, ECU firmware reverse, T-BOX telematics, EDR data extraction, and vehicle attack chain reconstruction.
---

# Vehicle / IoT Forensics

## Purpose

Analyze connected vehicle evidence (car.E01 images) to investigate accidents, reconstruct attack chains, detect CAN bus injection, reverse ECU firmware, extract T-BOX communications, and recover EDR (Event Data Recorder) data.

## Use When

- Vehicle forensic image (car.E01) is present in evidence
- CAN bus traffic analysis is required
- ECU firmware needs reverse engineering
- T-BOX telematics data needs extraction
- Collision/accident reconstruction is needed

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `car_image` | Yes | Vehicle forensic image (E01 or extracted files) |
| `dlt_log` | No | Diagnostic Log and Trace file |
| `can_traffic` | No | CAN bus traffic capture |
| `ecu_firmware` | No | ECU firmware binary files |

## Outputs

| Output | Description |
|--------|-------------|
| `attack_timeline` | Chronological attack reconstruction |
| `can_injections` | Detected CAN bus injection events |
| `malicious_firmware` | Identified firmware modifications |
| `edr_data` | Pre-collision vehicle state data |
| `c2_communications` | T-BOX remote control evidence |

## Workflow

### Step 1: Evidence Structure Mapping

```
car.E01 typical structure:
  system.dlt          — System diagnostic logs
  gateway_ecu.bin     — Gateway firmware
  engine_ecu.bin      — Engine control firmware
  bcm_ecu.bin         — Body control module
  adas_firmware.bin   — ADAS firmware
  tbox/               — T-BOX telematics data
  dashcam/            — Dashcam recordings
  databases/          — Vehicle browser/Bluetooth DBs
```

**Evidence**: Record `file_inventory`, `evidence_structure` in evidence ledger.

### Step 2: DLT Log Analysis

```
strings system.dlt | rg -i "CRC|error|fault|collision|brake|steering"
strings system.dlt | rg -i "LKA|ADAS|override|inject|spoof|attack"
```

Severity levels: INFO (normal), WARN (ADAS anomaly), ERR (CRC failure = injection), FATL (collision confirmed).

**Evidence**: Record `log_entries`, `severity_findings`, `attack_indicators` in evidence ledger.

### Step 3: CAN Bus Analysis

Common CAN IDs: 0x0A0 (steering), 0x1xx (brake/throttle), 0x2xx (wheel speed), 0x3xx (RPM)

Attack signatures:
- CRC validation failures → message tampering
- Abnormally high frequency → signal injection/suppression
- Missing MAC authentication → protocol weakness
- Unexpected IDs → malicious command injection

**Evidence**: Record `suspicious_can_ids`, `crc_failures`, `frequency_anomalies` in evidence ledger.

### Step 4: ECU Firmware Analysis

```
strings gateway_ecu.bin | rg -i "key|seed|master|crypto|auth"
strings engine_ecu.bin | rg -i "limit|max|speed|RPM|governor"
strings adas_firmware.bin | rg -i "threshold|min_speed|trigger|km/h"
```

Look for: speed limit values, ADAS trigger thresholds, seed/key algorithms, backdoor commands.

**Evidence**: Record `firmware_findings`, `hidden_parameters`, `trigger_conditions` in evidence ledger.

### Step 5: T-BOX Telematics

```
# Communication logs
tshark -r telemetry.pcap -Y "http" -T fields -e http.host -e http.request.uri

# Malicious callback detection:
# - HTTP GET disguised as media stream → /media/audio/playlist.m3u8
# - Reverse shell: "Reverse shell connected... root@starOS:~#"
# - Firmware download: http://C2_IP/malicious.bin
```

**Evidence**: Record `c2_ip`, `malicious_urls`, `reverse_shell_evidence` in evidence ledger.

### Step 6: EDR and Attack Chain

EDR (Event Data Recorder) captures pre-collision state: vehicle speed, brake status, throttle %, steering angle, seatbelt status, airbag deployment time.

Reconstruct full attack chain:
```
GitHub exploit → Bluetooth attack → T-BOX reverse shell →
stop security monitor → flash malicious firmware →
ADAS triggers at speed → CAN injection → collision → EDR capture
```

**Evidence**: Record `edr_readings`, `attack_chain`, `evidence_links` in evidence ledger.

## Evidence Requirements

| Field | When to Record | Example |
|-------|---------------|---------|
| `dlt_entry` | Step 2 | ERR: CRC failure on msg 0x0A0 |
| `can_injection` | Step 3 | ID 0x0A0 at abnormal 500Hz |
| `firmware_param` | Step 4 | Speed limit: 120 km/h, modified to 255 |
| `tbox_c2` | Step 5 | C2 at 185.23.45.67:443 |
| `edr_speed` | Step 6 | 87 km/h at impact, no braking |
| `attack_chain` | Step 6 | Full 9-step attack reconstruction |

## Handoff

**Passes to**: `timeline-reconstruction` (for event timeline), `answer-gate` (for conclusions)
**Data available**: DLT findings, CAN injections, firmware analysis, T-BOX communications, EDR data

## Stop Conditions

- Vehicle image is incomplete or corrupted
- CAN bus traffic is encrypted with unknown key
- ECU firmware uses proprietary obfuscation
- EDR data extraction requires manufacturer-specific tools

## Notes

- DLT is the primary log format — search for CRC errors first (indicate injection)
- CAN ID 0x0A0 is the most safety-critical (steering control)
- Gateway ECU seed/key algorithm is the key to understanding the security model
- T-BOX reverse shell is the most common remote attack vector
- Dashcam metadata.json integrity check: "FAILED" indicates tampering
- NFC/PKE key clone detection: same timestamp with two different key IDs
