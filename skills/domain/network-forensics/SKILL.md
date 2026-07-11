---
name: network-forensics
description: PCAP/PCAPNG traffic analysis, TLS decryption, covert channel detection, credential extraction, webshell traffic analysis, and attack attribution.
---

# Network Forensics

## Purpose

Analyze network traffic captures (PCAP/PCAPNG) to extract evidence: decrypt TLS sessions, detect covert channels, extract authentication credentials, decode webshell communication, and reconstruct attack timelines.

## Use When

- PCAP/PCAPNG file is present in evidence
- Network traffic analysis is required (HTTP, DNS, TCP, TLS, FTP, SMB)
- Covert channel or data exfiltration is suspected
- Webshell traffic (Behinder/Godzilla/AntSword) needs decryption

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `pcap_file` | Yes | Path to PCAP/PCAPNG file |
| `sslkeylog` | No | SSLKEYLOG file for TLS decryption |
| `rsa_key` | No | RSA private key for TLS decryption |
| `wordlist` | No | Wordlist for WPA/NTLMv2 cracking |

## Outputs

| Output | Description |
|--------|-------------|
| `credentials` | Extracted usernames, passwords, hashes |
| `covert_data` | Data extracted from covert channels |
| `webshell_traffic` | Decrypted webshell commands and responses |
| `attack_timeline` | Ordered list of attack events with timestamps |

## Workflow

### Step 1: Quick Reconnaissance

Run the "three strikes" for instant overview:
```
capinfos pcap_file && tshark -r pcap_file -q -z io,phs
strings pcap_file | rg -i "flag|ctf|password|secret|key|token|\{.*\}"
tshark -r pcap_file --export-objects http,./http_objects/
```

**Evidence**: Record `protocol_distribution`, `suspicious_strings`, `exported_objects` in evidence ledger.

### Step 2: TLS/SSL Decryption

Four methods in order of preference:
1. **Keylog file**: `tshark -r pcap -o "tls.keylog_file:sslkeys.log" -Y http`
2. **RSA private key**: `tshark -r pcap -o "tls.keys_list:ip,443,http,key.pem" -Y http`
3. **Weak RSA factorization**: Extract certificate, factor n, generate private key
4. **Coredump master key**: Search memory dump for `RSA Session-ID:...Master-Key:...`

**Evidence**: Record `decryption_method`, `decrypted_streams` in evidence ledger.

### Step 3: Covert Channel Detection

Check these channels in order:
1. **ICMP**: Payload length encodes ASCII (`tshark -T fields -e icmp.data_len`)
2. **DNS**: Tail bytes of queries, long subdomains (>52 chars = tunnel), binary oracle (NOERROR/NXDOMAIN)
3. **TCP Flags**: Abnormal flag combos (FIN+SYN), 6-bit flag → base64
4. **Time intervals**: Two-interval binary encoding (threshold ~50ms)
5. **HTTP upload**: Export objects, check for hidden data in uploads

**Evidence**: Record `channel_type`, `extracted_data`, `encoding_method` in evidence ledger.

### Step 4: Credential Extraction

```
HTTP Basic:   tshark -Y "http.authorization" -T fields -e http.authorization
FTP:          tshark -Y "ftp.request.command==USER||ftp.request.command==PASS"
NTLMv2:       tshark -Y "ntlmssp.messagetype==0x00000003" → hashcat -m 5600
SMTP/IMAP:    tshark -Y "smtp||imap||pop" -T fields -e smtp.req.command
```

**Evidence**: Record `protocol`, `username`, `password_hash`, `cracked_password` in evidence ledger.

### Step 5: Webshell Traffic Decoding

Identify encoding chains:
- **Behinder**: URL → Base64 → XOR
- **Godzilla**: URL → Base64×2 → Gzip → AES-ECB
- **AntSword**: URL → Base64 → plaintext

Extract payloads from HTTP POST bodies, decode using identified chain.

**Evidence**: Record `webshell_type`, `encryption_key`, `decoded_commands`, `c2_ip` in evidence ledger.

### Step 6: Attack Pattern Recognition

| Pattern | Signature | Filter |
|---------|-----------|--------|
| Port scan | Many SYN to different ports | `tshark -q -z conv,tcp` |
| Dir brute | Many 404s | `http.response.code==404` |
| SQL injection | UNION/SLEEP in URL | `strings pcap \| rg "UNION\|SLEEP"` |
| Reverse shell | `/bin/sh -i`, `nc -e` | TCP stream follow |
| DNS tunnel | Long subdomain + high freq | `dns.qry.name matches ".{52,}"` |

**Evidence**: Record `attack_type`, `source_ip`, `target_ip`, `timestamps` in evidence ledger.

## Evidence Requirements

| Field | When to Record | Example |
|-------|---------------|---------|
| `pcap_summary` | Step 1 | 1523 packets, 45 HTTP, 12 DNS |
| `protocol` | Every protocol found | HTTP, DNS, TLS, FTP |
| `ip_pair` | Every conversation | 192.168.1.5 → 10.0.0.1:443 |
| `credential` | Step 4 | FTP user: admin, pass: P@ssw0rd |
| `covert_channel` | Step 3 | ICMP length encoding, 42 bytes extracted |
| `webshell_key` | Step 5 | AES key: e45e329feb5d925b |
| `attack_event` | Step 6 | Port scan from 10.0.0.5 at 14:23:01 |

## Handoff

**Passes to**: `file-triage` (for exported objects), `answer-gate` (for conclusions)
**Data available**: Decrypted streams, extracted credentials, covert channel data, attack timeline

## Stop Conditions

- PCAP file is corrupted and cannot be repaired
- TLS decryption all four methods fail
- Covert channel detected but encoding is unknown custom scheme
- High-risk operation: cracking requires GPU resources not available

## Notes

- `--export-objects http` is the single most effective command — resolves 80% of HTTP challenges
- Always run `strings` before `tshark` — fastest coverage for simple flags
- ICMP covert channels are the most common — check payload length first
- DNS tunnels show as subdomains longer than 52 characters
- For large PCAPs, use `editcap -c 10000 big.pcap small.pcap` to split
- If PCAP won't open, try `pcapfix -d corrupted.pcap`
