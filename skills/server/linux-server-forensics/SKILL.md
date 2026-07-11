---
name: linux-server-forensics
description: Linux server system-level forensics — accounts, SSH history, shell history, cron jobs, systemd services, persistence mechanisms, and log analysis.
---

# Linux Server Forensics

## Purpose

Analyze Linux server systems for forensic evidence: user accounts, SSH access history, shell command history, scheduled tasks, systemd persistence, and system log analysis.

## Use When

- Linux server image needs system-level analysis
- User account and access audit is required
- Persistence mechanism detection is needed
- System log timeline reconstruction is required

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `server_root` | Yes | Path to mounted server filesystem or live SSH session |
| `target_user` | No | Specific user to investigate (default: all) |

## Outputs

| Output | Description |
|--------|-------------|
| `account_audit` | User accounts, groups, sudo access |
| `ssh_history` | SSH logins, authorized keys, known hosts |
| `command_history` | Shell commands executed by users |
| `persistence` | Cron jobs, systemd services, SSH keys |
| `log_timeline` | Chronological system events |

## Workflow

### Step 1: Account Audit

```
cat /etc/passwd              # All users (UID≥1000 = normal users)
cat /etc/shadow              # Password hashes (requires root)
cat /etc/group               # Groups
grep -i sudo /etc/group      # Sudo users
last -a                      # Login history
lastb -a                     # Failed logins
```

**Evidence**: Record `user_list`, `sudo_users`, `login_history`, `failed_logins` in evidence ledger.

### Step 2: SSH Forensics

```
cat /var/log/auth.log | grep "Accepted"     # Successful SSH
cat /var/log/auth.log | grep "Failed"       # Failed attempts
cat ~/.ssh/authorized_keys                  # Authorized public keys
cat ~/.ssh/known_hosts                      # Connected hosts
```

**Evidence**: Record `ssh_logins`, `authorized_keys`, `brute_force_attempts` in evidence ledger.

### Step 3: Command History

```
cat ~/.bash_history         # Bash history
cat ~/.zsh_history          # Zsh history
cat ~/.mysql_history        # MySQL commands
cat ~/.python_history       # Python commands
```

Focus on: curl/wget (downloads), git clone, pip/apt (installs), openssl/encrypt/decrypt.

**Evidence**: Record `suspicious_commands`, `downloaded_files`, `installed_packages` in evidence ledger.

### Step 4: Persistence Detection

```
crontab -l                  # User cron
ls /etc/cron.*              # System cron
systemctl list-unit-files --state=enabled  # Enabled services
ls /etc/systemd/system/     # Custom systemd units
cat /etc/rc.local           # Startup script
ls ~/.config/autostart/     # Desktop autostart
```

**Evidence**: Record `cron_jobs`, `enabled_services`, `startup_scripts` in evidence ledger.

### Step 5: Log Analysis

```
/var/log/auth.log           # Authentication events
/var/log/syslog             # General system log
/var/log/kern.log           # Kernel events
/var/log/nginx/             # Web server logs
/var/log/mysql/             # Database logs
journalctl --no-pager       # Systemd journal
```

**Evidence**: Record `log_events`, `error_patterns`, `security_events` in evidence ledger.

## Handoff

**Passes to**: `webapp-server-forensics` (for web analysis), `database-server-forensics` (for DB analysis)
**Data available**: Account audit, SSH history, command history, persistence findings, log timeline

## Notes

- Focus on UID 0 (root) and sudo group members first
- SSH authorized_keys is the most common persistence mechanism
- bash_history may be truncated or cleared — check .bash_history.* backups
- Cron entries with curl/wget are strong indicators of malicious persistence
- systemd service files in /etc/systemd/system/ override defaults — check these first
