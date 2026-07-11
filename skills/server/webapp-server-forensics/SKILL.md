---
name: webapp-server-forensics
description: Web application server forensics — Nginx/Apache/IIS config analysis, webshell detection, access log analysis, and web framework artifact extraction.
---

# Web Application Server Forensics

## Purpose

Analyze web application servers for forensic evidence: web server configuration, webshell detection, access log analysis, framework-specific artifacts, and attack attribution from web logs.

## Use When

- Nginx/Apache/IIS/Tomcat configuration needs analysis
- Webshell detection is required
- Web access logs need forensic analysis
- Web framework (WordPress/ThinkPHP/Laravel/Spring) artifacts need extraction

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `web_root` | Yes | Web root directory path |
| `log_path` | Yes | Web server log directory |
| `web_server_type` | No | nginx/apache/iis/tomcat (auto-detect if omitted) |

## Outputs

| Output | Description |
|--------|-------------|
| `web_config` | Server configuration (vhosts, SSL, upstream) |
| `webshells` | Detected backdoor files |
| `access_analysis` | Attack patterns from access logs |
| `framework_info` | CMS/framework identification and config |

## Workflow

### Step 1: Configuration Analysis

```
# Nginx
cat /etc/nginx/nginx.conf
ls /etc/nginx/sites-enabled/
cat /etc/nginx/vhost/*.conf

# Apache
cat /etc/apache2/apache2.conf
ls /etc/apache2/sites-enabled/

# 宝塔 Panel
cat /www/server/panel/vhost/nginx/*.conf
cat /www/server/panel/vhost/apache/*.conf
```

Extract: server names, upstream backends, SSL certs, proxy configurations, DB connection strings.

**Evidence**: Record `server_config`, `vhosts`, `upstream_targets`, `db_connections` in evidence ledger.

### Step 2: Webshell Detection

```
# Recently modified scripts
find /www/wwwroot/ -name "*.php" -mtime -7
find /www/wwwroot/ -name "*.jsp" -mtime -7

# Suspicious patterns
grep -rn "eval\(.*\$_\(GET\|POST\|REQUEST\)" /www/wwwroot/
grep -rn "base64_decode\|system\|passthru\|shell_exec" /www/wwwroot/
grep -rn "assert\(\$_" /www/wwwroot/

# Image-embedded webshell
grep -rn "exif_imagetype\|getimagesize\|imagecreatefrom" /www/wwwroot/
```

**Evidence**: Record `webshell_files`, `webshell_type`, `webshell_timestamps` in evidence ledger.

### Step 3: Access Log Analysis

```
# Extract attack IPs
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -20

# Find webshell access
grep -E "POST.*\.(php|jsp|asp)" access.log | head -50

# Find directory brute force
grep " 404 " access.log | awk '{print $7}' | sort | uniq -c | sort -rn

# Find SQL injection
grep -i "union\|select\|sleep\|benchmark" access.log
```

**Evidence**: Record `attack_ips`, `attack_patterns`, `webshell_access_times` in evidence ledger.

### Step 4: Framework-Specific Analysis

```
# WordPress
cat wp-config.php | grep DB_

# ThinkPHP
cat application/database.php

# Laravel
cat .env | grep DB_

# Spring Boot
cat application.properties | grep spring.datasource

# 宝塔
cat /www/server/panel/data/default.db  # SQLite panel database
```

**Evidence**: Record `framework_type`, `db_config`, `admin_paths` in evidence ledger.

## Handoff

**Passes to**: `database-server-forensics` (for DB analysis), `answer-gate` (for conclusions)
**Data available**: Web config, detected webshells, attack patterns, framework credentials

## Notes

- 宝塔 panel is high-frequency in Chinese competitions — /www/server/panel/ path
- Webshell access patterns: periodic POST requests to .php/.jsp files
- Attack timeline: scan → brute force → upload webshell → execute commands
- Check both access.log and error.log for complete picture
- Proxy configurations (nginx upstream) reveal backend server topology
