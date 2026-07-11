---
name: database-server-forensics
description: Database server forensics — MySQL/PostgreSQL/Redis/MongoDB/SQLite analysis, binlog recovery, credential extraction, and data export.
---

# Database Server Forensics

## Purpose

Analyze database servers for forensic evidence: extract credentials, dump databases, analyze transaction logs, recover deleted data, and correlate database artifacts with web application activity.

## Use When

- Database server (MySQL/PostgreSQL/Redis/MongoDB/SQLite) needs analysis
- Database credentials need extraction
- Transaction logs need analysis for data recovery
- Deleted records need recovery from binary logs

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `db_type` | Yes | mysql / postgresql / redis / mongodb / sqlite |
| `db_data_path` | Yes | Database data directory or dump file |
| `target_tables` | No | Specific tables to investigate |

## Outputs

| Output | Description |
|--------|-------------|
| `db_dump` | Full database export |
| `credentials` | Extracted database credentials |
| `deleted_records` | Recovered deleted data from logs |
| `audit_findings` | Suspicious queries or data access |

## Workflow

### Step 1: Credential Extraction

```
# MySQL
cat /etc/mysql/debian.cnf
cat /etc/mysql/my.cnf | grep -i password
cat ~/.my.cnf

# PostgreSQL
cat /etc/postgresql/*/main/pg_hba.conf
cat ~/.pgpass

# Redis
cat /etc/redis/redis.conf | grep requirepass

# MongoDB
cat /etc/mongod.conf | grep -A5 security

# Application config
grep -rn "DB_PASSWORD\|db_password\|MYSQL_PWD" /www/
```

**Evidence**: Record `db_type`, `credentials`, `connection_strings` in evidence ledger.

### Step 2: Database Dump

```
# MySQL
mysqldump --all-databases > all_db.sql
mysql -e "SELECT * FROM information_schema.tables"

# PostgreSQL
pg_dumpall > pg_all.sql

# Redis
redis-cli BGSAVE
cp /var/lib/dump.rdb ./redis_dump.rdb

# MongoDB
mongodump --out ./mongo_dump/

# SQLite
sqlite3 database.db .dump > db_dump.sql
```

**Evidence**: Record `dump_hash`, `table_count`, `record_counts` in evidence ledger.

### Step 3: Binary Log Analysis (MySQL)

```
# List binary logs
mysqlbinlog --list-binary-logs

# Read specific log
mysqlbinlog --base64-output=DECODE-ROWS -v mysql-bin.000001

# Find DELETE/UPDATE operations
mysqlbinlog mysql-bin.000001 | grep -i "DELETE\|UPDATE\|DROP"

# Recover deleted records
mysqlbinlog --start-datetime="2026-01-15 00:00:00" --stop-datetime="2026-01-16 00:00:00" mysql-bin.000001
```

**Evidence**: Record `binlog_entries`, `deleted_data`, `recovery_timestamps` in evidence ledger.

### Step 4: Data Analysis

```
# List databases
mysql -e "SHOW DATABASES"

# Check user tables
mysql -e "SELECT user, host, authentication_string FROM mysql.user"

# Check recent activity
mysql -e "SELECT * FROM information_schema.processlist"

# Redis key analysis
redis-cli KEYS "*"
redis-cli INFO keyspace
```

**Evidence**: Record `database_list`, `user_accounts`, `suspicious_queries` in evidence ledger.

## Handoff

**Passes to**: `answer-gate` (for conclusions), `timeline-reconstruction` (for event correlation)
**Data available**: Database dumps, credentials, deleted records, audit findings

## Notes

- MySQL binlog is the most valuable source for recovering deleted data
- Redis RDB files contain point-in-time snapshots — compare with AOF for timeline
- SQLite databases in app directories often contain more data than the main DB server
- Database passwords often match web application credentials
- Check database user privileges — GRANT ALL on sensitive databases is suspicious
