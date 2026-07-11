---
name: stego
description: Image, audio, video, and document steganography detection and extraction including LSB, frequency domain, metadata hiding, and encoding steganography.
---

# Steganography

## Purpose

Detect and extract hidden data from images, audio, video, documents, and text using steganography analysis techniques including LSB detection, steghide extraction, frequency analysis, and encoding steganography.

## Use When

- Image/audio/video file is suspected of containing hidden data
- Challenge involves steganography (LSB, steghide, binwalk, etc.)
- QR/barcode with damaged or hidden content
- Document with whitespace, zero-width, or metadata hiding

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `target_file` | Yes | File to analyze for hidden data |
| `password` | No | Password for steghide extraction |
| `wordlist` | No | Wordlist for steghide brute force |

## Outputs

| Output | Description |
|--------|-------------|
| `hidden_data` | Extracted hidden content |
| `stego_method` | Identified steganography technique |
| `nested_files` | Files embedded within the target |

## Workflow

### Step 1: Quick Scan (30 seconds)

```
strings target_file | rg -i "flag|ctf|secret|password|key|\{.*\}"
exiftool -a -u -g1 target_file | rg -i "flag|ctf|comment|artist|description"
```

**Evidence**: Record `suspicious_strings`, `metadata_findings` in evidence ledger.

### Step 2: Structure Analysis

```
binwalk -e target_file            # Embedded file extraction
7z l target_file                  # Archive listing
pngcheck -v target_file           # PNG chunk verification (if PNG)
```

**Evidence**: Record `embedded_files`, `archive_structure`, `chunk_anomalies` in evidence ledger.

### Step 3: LSB Detection

```
zsteg -a target_file              # PNG/BMP LSB scan (all channels)
zsteg -a -v target_file           # Verbose output
```

For manual analysis: separate RGB channels, examine LSB planes.

**Evidence**: Record `lsb_channels`, `extracted_lsb_data` in evidence ledger.

### Step 4: Steghide Analysis

```
steghide info target_file         # Check if steghide data exists
steghide extract -sf target_file -p password
stegseek target_file wordlist.txt # Brute force password
```

**Evidence**: Record `steghide_detected`, `password`, `extracted_data` in evidence ledger.

### Step 5: Color/Channel Analysis

```
magick target_file -separate channel_%d.png     # Channel separation
magick target_file -channel B -evaluate And 1 blue_lsb.png  # Specific plane
magick target_file -auto-level -equalize enhanced.png       # Contrast enhancement
magick compare img1.png img2.png diff.png       # Image diff
```

**Evidence**: Record `channel_findings`, `diff_analysis` in evidence ledger.

### Step 6: Specialized Checks

**PNG**: Height CRC brute force (hidden content below visible area), APNG frames, chunk reorder
**GIF**: Frame differencing → Morse code detection
**Audio**: Spectrogram (`ffmpeg -i audio.wav -lavfi showspectrumpic=s=1024x512 spec.png`), slow/reverse, DTMF
**Video**: Frame extraction (`ffmpeg -i video.mp4 -vf "fps=1" frames/%04d.png`), multi-stream
**Document**: Zero-width characters (`rg $'\u200b|\u200c|\u200d'`), whitespace encoding
**PDF**: `mutool clean -d` to decompress streams, `pdfimages` for hidden images
**QR**: `zbarimg` for reading, manual repair for damaged codes

**Evidence**: Record `specialized_method`, `findings` in evidence ledger.

## Evidence Requirements

| Field | When to Record | Example |
|-------|---------------|---------|
| `file_type` | Step 1 | PNG, 800x600, 24-bit |
| `metadata` | Step 1 | Comment: "password is 1234" |
| `embedded` | Step 2 | ZIP at offset 0x1A3F |
| `lsb_data` | Step 3 | Channel R LSB: 384 bytes extracted |
| `steghide_pass` | Step 4 | Password: "hello" |
| `hidden_content` | Any step | flag{steg0_1s_fun} |

## Handoff

**Passes to**: `file-triage` (for nested files), `crypto` (for encrypted hidden data), `answer-gate` (for conclusions)
**Data available**: Hidden data, stego method, nested files, passwords

## Stop Conditions

- All standard tools yield no results and no clear stego indicators exist
- Steghide brute force exhausted wordlist without success
- Encrypted content with no key available
- Visual steganography requiring specialized hardware analysis

## Notes

- `strings` + `exiftool` first — these two steps often find flags directly
- File size anomaly: 2MB image with tiny dimensions → likely hidden data
- LSB may be in bit 2 or 3, not just bit 0
- For Angecryption: AES-CBC encrypt file A → valid file B, decrypt B to get A
- Base65536: CJK character wall = 2 bytes/char, `pip install base65536`
- Esoteric languages: Brainfuck (`+++++++[>...`), Whitespace (only spaces/tabs/newlines), Piet (colored pixels)
