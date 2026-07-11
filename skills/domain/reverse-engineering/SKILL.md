---
name: reverse-engineering
description: Binary reverse engineering for CTF challenges including disassembly with radare2, unpacking, string analysis, function identification, and common RE challenge patterns.
---

# Reverse Engineering

## Purpose

Analyze binary executables (PE/ELF) to understand their logic, extract hidden data, and reverse custom algorithms: perform static disassembly, identify key functions, unpack binaries, and recover flags from compiled programs.

## Use When

- Binary executable (PE/ELF) is present in evidence
- CTF reverse engineering challenge requires analysis
- Packed/obfuscated binary needs unpacking
- Custom encryption algorithm needs reversing

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `binary` | Yes | Path to binary executable |
| `architecture` | No | x86, x86-64, ARM (auto-detected if omitted) |
| `debug_symbols` | No | Whether debug symbols are present |

## Outputs

| Output | Description |
|--------|-------------|
| `strings_of_interest` | Suspicious strings (flag, password, key) |
| `key_functions` | Identified encryption, comparison, validation functions |
| `algorithm` | Reversed custom algorithm logic |
| `extracted_data` | Hidden data extracted from binary |

## Workflow

### Step 1: Initial Reconnaissance

```
file binary                    # File type and architecture
rabin2 -I binary               # Detailed binary info
rabin2 -z binary               # Strings with addresses
rabin2 -i binary               # Import functions
rabin2 -E binary               # Export functions
```

Quick string scan:
```
strings binary | rg -i "flag|ctf|correct|wrong|password|key|secret|congratulations"
strings binary | rg -i "/bin/sh|system|exec"
```

**Evidence**: Record `file_type`, `architecture`, `suspicious_strings`, `import_functions` in evidence ledger.

### Step 2: Disassembly with radare2

```
r2 -A binary                   # Auto-analyze
aaa                            # Full analysis
afl                            # List all functions
s main                         # Go to main
pdf                            # Disassemble function
iz                             # List strings with addresses
ii                             # List imports
axt <addr>                     # Cross-references to address
```

One-liner for quick analysis:
```
r2 -A -q -c 'aaa; afl; iz; pdc @ main' binary
```

**Evidence**: Record `function_list`, `main_logic`, `string_locations` in evidence ledger.

### Step 3: Key Function Location

Find comparison/validation functions:
```
r2 -A -q -c 'axt sym.imp.strcmp' binary    # strcmp references
r2 -A -q -c 'axt sym.imp.strncmp' binary   # strncmp references
```

Approach: find "Correct!" string → `axt <addr>` → trace back to validation logic.

**Evidence**: Record `validation_function`, `comparison_data`, `expected_value` in evidence ledger.

### Step 4: Unpacking

```
upx -d packed.exe -o unpacked.exe    # UPX unpack
upx -t packed.exe                     # Test if UPX
rabin2 -I binary | rg "packer"        # Check other packers
```

Manual unpacking: find OEP → set breakpoint → run → memory dump.

**Evidence**: Record `packer_type`, `original_entry_point`, `unpacked_binary` in evidence ledger.

### Step 5: Data Extraction

```
r2 -q -c "/ flag{" binary             # Search for flag string
r2 -q -c "px 256 @ 0x402000" binary   # Hex dump at offset
rabin2 -O binary                       # Extractable sections
```

**Evidence**: Record `extracted_data`, `data_offset`, `data_type` in evidence ledger.

### Step 6: Algorithm Reversing

Common patterns:
- **TEA/XTEA**: Look for magic constant `0x9E3779B9`
- **RC4**: Look for 256-byte S-box initialization
- **Custom XOR**: Find XOR loop, extract key
- **VM-based**: Identify opcode table → disassemble VM bytecode → trace execution

Write inverse Python script to recover plaintext.

**Evidence**: Record `algorithm_type`, `key_parameters`, `inverse_script` in evidence ledger.

## Evidence Requirements

| Field | When to Record | Example |
|-------|---------------|---------|
| `binary_info` | Step 1 | ELF x86-64, stripped, not packed |
| `key_string` | Step 1 | "Enter password:" at 0x402000 |
| `function_addr` | Step 2 | main: 0x401136, check: 0x4011a0 |
| `comparison` | Step 3 | strcmp(input, "flag{r3vers3_m3}") |
| `algorithm` | Step 6 | TEA encryption, 32 rounds, key at 0x403000 |
| `recovered_flag` | Step 6 | flag{r3vers3_m3} |

## Handoff

**Passes to**: `crypto` (for identified encryption), `answer-gate` (for conclusions)
**Data available**: Reversed algorithm, extracted data, recovered flag

## Stop Conditions

- Binary is heavily obfuscated with no clear logic
- Anti-analysis checks prevent disassembly
- Custom VM with unknown instruction set
- Required dynamic analysis environment not available

## Notes

- `strings` first — 40% of RE flags are plaintext in the binary
- `rabin2 -z` gives addresses unlike plain `strings`
- XOR is the most common obfuscation — find the XOR loop and key
- `axt` cross-references are essential for tracing from strings to code
- Pay attention to `strcmp` calls — they usually validate input
- `rax2` for quick number conversions: `rax2 0x41414141`, `rax2 -S AAAA`
