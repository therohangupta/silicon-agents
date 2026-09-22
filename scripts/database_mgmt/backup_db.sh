#!/bin/bash
# Backup the Docker Postgres database using pg_dump inside the Compose db container.
# Reads DB config from packages/config.py (single source of truth).
#
# Prefer this over scripts/backup_db.sh when Postgres only exists in Compose,
# so the dump client matches the server major version.

# Absolute directory containing this script (scripts/database_mgmt/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Parent of database_mgmt is scripts/ (historical REPO_ROOT naming preserved).
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Extract DB_HOST from Python config (used for log context; dump uses the container).
DB_HOST=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_HOST; print(DB_HOST)")
# Extract DB_PORT from Python config.
DB_PORT=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_PORT; print(DB_PORT)")
# Extract DB_USER for pg_dump -U inside the container.
DB_USER=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_USER; print(DB_USER)")
# Extract DB_NAME for pg_dump -d inside the container.
DB_NAME=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_NAME; print(DB_NAME)")

# Unique suffix so repeated backups do not overwrite each other.
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
# Dump directory under REPO_ROOT (scripts/db_backups when REPO_ROOT is scripts/).
BACKUP_DIR="$REPO_ROOT/db_backups"
# Ensure the dump directory exists.
mkdir -p "$BACKUP_DIR"

# Operator-facing progress line.
echo "Backing up $DB_NAME from $DB_HOST:$DB_PORT..."
# Use pg_dump from the container to avoid version mismatch with the host client.
docker compose exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/${DB_NAME}_$TIMESTAMP.sql"

# Branch on docker/pg_dump exit status.
if [ $? -eq 0 ]; then
    # Success path: report the dump path.
    echo "Backed up to $BACKUP_DIR/${DB_NAME}_$TIMESTAMP.sql"
else
    # Failure path for operators/CI.
    echo "Backup failed!" >&2
    exit 1
fi
