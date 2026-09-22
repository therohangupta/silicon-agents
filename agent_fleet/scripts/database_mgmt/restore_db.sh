#!/bin/bash
# Restore the Docker Postgres database from a backup file.
# Reads DB config from packages/config.py (single source of truth).
#
# Usage: ./restore_db.sh <backup_file.sql>
# Example: ./restore_db.sh ../db_backups/agent_fleet_20240123_143052.sql
#
# Streams SQL into `psql` inside the Compose `db` container (-T for non-TTY)
# so client/server versions match.

# Require a backup file argument.
if [ -z "$1" ]; then
    # Tell the operator how to invoke the script.
    echo "Usage: $0 <backup_file.sql>" >&2
    echo "Example: $0 ../db_backups/agent_fleet_20240123_143052.sql" >&2
    exit 1
fi

# Capture the path from argv.
BACKUP_FILE="$1"
# Fail fast if the dump is missing (wrong path / typo).
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

# Absolute directory containing this script (scripts/database_mgmt/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Parent of database_mgmt is scripts/ (historical REPO_ROOT naming preserved).
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Extract DB_HOST for log context.
DB_HOST=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_HOST; print(DB_HOST)")
# Extract DB_PORT for log context.
DB_PORT=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_PORT; print(DB_PORT)")
# Extract DB_USER for psql -U inside the container.
DB_USER=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_USER; print(DB_USER)")
# Extract DB_NAME for psql -d inside the container.
DB_NAME=$(python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT'); from packages.config import DB_NAME; print(DB_NAME)")

# Operator-facing progress line before the potentially destructive restore.
echo "Restoring $DB_NAME on $DB_HOST:$DB_PORT from $BACKUP_FILE..."
# Use psql from the container to avoid version mismatch; stdin is the dump file.
docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"

# Branch on psql exit status.
if [ $? -eq 0 ]; then
    # Success path.
    echo "Restore complete."
else
    # Failure path for operators/CI.
    echo "Restore failed!" >&2
    exit 1
fi
