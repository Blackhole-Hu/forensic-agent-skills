---
name: android-analysis
description: Android APK reverse engineering and mobile forensics including decompilation, manifest audit, native library analysis, dynamic analysis, and app-specific artifact extraction.
---

# Android Analysis

## Purpose

Analyze Android applications (APK) for CTF challenges and forensic investigations: decompile bytecode, audit permissions and components, reverse native libraries, extract app data, and identify security-relevant findings.

## Use When

- APK file is present in evidence
- Android device image requires app-level analysis
- Mobile forensics requires app data extraction
- CTF challenge involves Android reverse engineering

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `apk_file` | Yes | Path to APK file |
| `device_image` | No | Android device image for forensic extraction |
| `target_package` | No | Specific package name to investigate |

## Outputs

| Output | Description |
|--------|-------------|
| `app_info` | Package name, version, permissions, components |
| `source_code` | Decompiled Java source |
| `native_libs` | Native .so analysis results |
| `secrets` | Hardcoded keys, passwords, API endpoints |
| `app_data` | Extracted databases, preferences, logs |

## Workflow

### Step 1: Unpack and Scan

```
7z x app.apk -oapk_extracted/    # APK is ZIP format
strings app.apk | rg -i "flag|ctf|password|secret|key|api|http"
strings app.apk | rg "flag\{.*\}"
```

Key files: `AndroidManifest.xml`, `classes.dex`, `lib/`, `res/`, `assets/`, `META-INF/`

**Evidence**: Record `package_structure`, `suspicious_strings` in evidence ledger.

### Step 2: Decompile with jadx

```
jadx -d output_dir/ app.apk
rg -n "flag|password|secret|key" output_dir/sources/
rg -n "http://|https://" output_dir/sources/
rg -n "Cipher|encrypt|decrypt|AES|RSA" output_dir/sources/
rg -n "System\.loadLibrary|native " output_dir/sources/
```

**Evidence**: Record `decompiled_sources`, `sensitive_code_locations` in evidence ledger.

### Step 3: Manifest Audit

Check `AndroidManifest.xml` for:
- Permissions (dangerous: READ_SMS, CAMERA, LOCATION)
- Exported components (activities, services, receivers)
- `debuggable="true"` flag
- `allowBackup="true"` flag
- Intent filters

**Evidence**: Record `permissions`, `exported_components`, `security_flags` in evidence ledger.

### Step 4: Native Library Analysis

```
fd "\.so$" apk_extracted/lib/              # List native libs
rabin2 -I lib/arm64-v8a/libnative.so      # Binary info
strings libnative.so | rg -i "flag|key"    # String scan
rabin2 -E libnative.so | rg "Java_"        # JNI exports
```

For JNI functions: `r2 -A -q -c "s sym.Java_com_example_checkFlag; pdf" libnative.so`

**Evidence**: Record `native_libs`, `jni_functions`, `native_secrets` in evidence ledger.

### Step 5: Resource and Data Extraction

```
# Assets (often hide flags)
fd . apk_extracted/assets/ -t f
rg "flag|ctf" apk_extracted/res/values/strings.xml

# SQLite databases (if present)
sqlite3 app.db .dump

# Shared preferences (config/secrets)
cat apk_extracted/shared_prefs/*.xml
```

**Evidence**: Record `resource_findings`, `database_contents`, `preferences` in evidence ledger.

### Step 6: Dynamic Analysis (if emulator available)

```
adb install app.apk
adb logcat | rg -i "flag|ctf"
adb shell run-as com.app cat /data/data/com.app/shared_prefs/*.xml
adb shell run-as com.app cp /data/data/com.app/databases/app.db /sdcard/
```

**Evidence**: Record `runtime_logs`, `app_data_contents` in evidence ledger.

## Evidence Requirements

| Field | When to Record | Example |
|-------|---------------|---------|
| `package_name` | Step 2 | com.example.ctfapp |
| `permissions` | Step 3 | READ_EXTERNAL_STORAGE, CAMERA |
| `hardcoded_key` | Step 2 | AES key: "MySecretKey123" |
| `native_func` | Step 4 | Java_com_example_checkFlag |
| `database` | Step 5 | users.db with credentials |
| `flag_found` | Any step | flag{andr01d_r3vers3} |

## Handoff

**Passes to**: `reverse-engineering` (for native .so), `crypto` (for encryption), `answer-gate` (for conclusions)
**Data available**: Decompiled source, native analysis, app data, extracted secrets

## Stop Conditions

- APK is heavily obfuscated (ProGuard/R8) with no meaningful class names
- Native library uses advanced anti-reverse techniques
- Dynamic analysis requires physical device not available
- Flutter app with encrypted assets

## Notes

- APK = ZIP, always `7z x` first
- `strings` on whole APK is faster than decompiling for simple flags
- Check `assets/` and `res/raw/` — flags often hide there
- ProGuard obfuscation: a.b.c.d class names — follow method calls not names
- Flutter apps: look for `libflutter.so`, `flutter_assets/`, check `shared_prefs` for DB passwords
- SQLCipher: PBKDF2WithHmacSHA256, key from shared_prefs
- HarmonyOS: `.app` → rename to `.zip` → extract `.hap` → `abc-decompiler`
