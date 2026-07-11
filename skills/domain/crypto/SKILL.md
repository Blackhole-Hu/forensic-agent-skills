---
name: crypto
description: CTF cryptography analysis including encoding identification, classical ciphers, hash cracking, RSA attacks, and forensic password recovery.
---

# Cryptography

## Purpose

Identify, decode, and break cryptographic protections in CTF challenges and forensic scenarios: identify encoding types, break classical ciphers, crack hash values, execute RSA attacks, and recover passwords from captured data.

## Use When

- Encoded/encrypted data is present (Base64, Hex, XOR, RSA, etc.)
- Hash values need cracking (MD5, SHA1, SHA256, NTLM, bcrypt)
- Password-protected files need opening (ZIP, PDF, Office, VeraCrypt)
- RSA parameters (n, e, c) are available for analysis

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `cipher_data` | Yes | Encoded/encrypted data to analyze |
| `cipher_type` | No | Known or suspected cipher type |
| `known_plaintext` | No | Known plaintext for known-plaintext attacks |
| `wordlist` | No | Wordlist for dictionary attacks |

## Outputs

| Output | Description |
|--------|-------------|
| `plaintext` | Decoded/decrypted content |
| `cipher_type` | Identified cipher or encoding |
| `key` | Recovered encryption key or password |

## Workflow

### Step 1: Encoding Identification

| Pattern | Type | Decode |
|---------|------|--------|
| `[A-Za-z0-9+/=]+` | Base64 | `base64 -d` / `openssl base64 -d` |
| `[A-Z2-7=]+` | Base32 | `base32 -d` |
| `[0-9a-fA-F]+` | Hex | `xxd -r -p` |
| `[1-9A-HJ-NP-Za-km-z]+` | Base58 | Python `base58` |
| `%XX%XX` | URL encoding | `urllib.parse.unquote()` |
| `.-` combos | Morse | Lookup table |
| `n=, e=, c=` | RSA | See Step 4 |

**Evidence**: Record `encoding_type`, `raw_data`, `decoded_data` in evidence ledger.

### Step 2: Classical Ciphers

**Caesar brute force**: Try all 25 shifts, check for readable text.
**Vigenere**: Guess key length from repeated patterns, frequency analysis per position.
**Substitution**: Frequency analysis — English most common: E, T, A, O, I, N.

**Evidence**: Record `cipher_type`, `key`, `plaintext` in evidence ledger.

### Step 3: Hash Cracking

| Hash | Length | hashcat mode |
|------|--------|-------------|
| MD5 | 32 hex | 0 |
| SHA1 | 40 hex | 100 |
| SHA256 | 64 hex | 1400 |
| SHA512 | 128 hex | 1700 |
| NTLM | 32 hex | 1000 |
| bcrypt | `$2a$...` | 3200 |
| SHA512 crypt | `$6$...` | 1800 |

```
hashcat -m 0 -a 0 hash.txt wordlist.txt              # Dictionary
hashcat -m 0 -a 0 hash.txt wordlist.txt -r best64.rule  # Rules
hashcat -m 0 -a 3 hash.txt "flag{?l?l?l?l?l}"        # Mask
```

Check online first: crackstation.net, hashes.com.

**Evidence**: Record `hash_type`, `hash_value`, `cracked_password`, `method` in evidence ledger.

### Step 4: RSA Attacks

| Condition | Attack |
|-----------|--------|
| Small e (e=3) | Cube root: `gmpy2.iroot(c, 3)` |
| Same n, different e | Common modulus: `gcd(e1, e2)` → extended Euclidean |
| Small d | Wiener attack |
| p ≈ q | Fermat factorization |
| Known p, q | Direct: `d = inverse(e, (p-1)*(q-1))` |

```
openssl rsa -pubin -in public.pem -text -noout  # Extract parameters
python RsaCtfTool.py --publickey public.pem --uncipherfile flag.enc
```

**Evidence**: Record `n`, `e`, `c`, `p`, `q`, `d`, `plaintext` in evidence ledger.

### Step 5: Forensic Password Recovery

**Priority order for passwords**:
1. Competition/platform name (DIDCTF, pgs, meiya)
2. Default passwords (123456, admin, password)
3. Challenge description keywords
4. Content from other files in same evidence
5. Short numeric passwords (4-6 digits, john quick brute)

**Known-plaintext ZIP attack**: If a file with known content exists in the ZIP, use ARCHPR/AZPR to recover the key via CRC32 collision.

**Evidence**: Record `password_source`, `password`, `target_file` in evidence ledger.

## Evidence Requirements

| Field | When to Record | Example |
|-------|---------------|---------|
| `encoding_type` | Step 1 | Base64 |
| `decoded_data` | Step 1 | SGVsbG8= → Hello |
| `hash_type` | Step 3 | MD5 (32 hex) |
| `cracked_value` | Step 3 | 5f4dcc3b5aa765d61d8327deb882cf99 → password |
| `rsa_params` | Step 4 | n=..., e=65537, c=... |
| `recovered_key` | Step 4 | d=..., plaintext=flag{...} |

## Handoff

**Passes to**: `file-triage` (for decrypted files), `answer-gate` (for conclusions)
**Data available**: Decrypted content, recovered passwords, identified algorithms

## Stop Conditions

- Hash type cannot be identified
- RSA parameters insufficient for any known attack
- Brute force space too large without GPU
- Encryption uses unknown custom algorithm

## Notes

- Base64 trailing `=` is the most obvious encoding marker
- Multi-layer encoding is common: Hex → Base64 → Base32 → plaintext
- Use CyberChef (gchq.github.io/CyberChef) for unknown encodings
- Online rainbow tables before local cracking: crackstation.net
- XOR with repeating key: find key length via Kasiski examination, then frequency analysis per position
- Cryptocurrency wallet: 12-word mnemonic may be in IME custom phrases, notes, or diary
