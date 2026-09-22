#!/bin/bash
# Backup the Docker Postgres database from the host using local pg_dump.
# Reads DB config from packages/config.py (single source of truth) so this
# script cannot drift from the app's connection settings.
#
# Note: prefer database_mgmt/backup_db.sh when the DB runs only inside Compose
# (avoids client/server version skew by using the container's pg_dump).

# Absolute directory containing this script (scripts/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# agent_fleet repo root (parent of scripts/).
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Extract DB_HOST from Python config (single source of truth).
DB_HOST=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_HOST; print(DB_HOST)")
# Extract DB_PORT from Python config.
DB_PORT=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_PORT; print(DB_PORT)")
# Extract DB_USER from Python config.
DB_USER=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_USER; print(DB_USER)")
# Extract DB_NAME from Python config.
DB_NAME=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_NAME; print(DB_NAME)")

# Unique suffix so repeated backups do not overwrite each other.
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
# Dump directory under the repo root (gitignored / not documented as source).
BACKUP_DIR="$REPO_ROOT/db_backups"
# Ensure the dump directory exists.
mkdir -p "$BACKUP_DIR"

# Operator-facing progress line before the potentially long dump.
echo "Backing up $DB_NAME from $DB_HOST:$DB_PORT..."
# Stream SQL dump from the reachable Postgres into a timestamped file.
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/${DB_NAME}_$TIMESTAMP.sql"

# Branch on pg_dump exit status.
if [ $? -eq 0 ]; then
    # Success path: tell the operator where the file landed.
    echo "Backed up to $BACKUP_DIR/${DB_NAME}_$TIMESTAMP.sql"
else
    # Failure path: stderr message and non-zero exit for CI/scripts.
    echo "Backup failed!" >&2
    exit 1
fi
