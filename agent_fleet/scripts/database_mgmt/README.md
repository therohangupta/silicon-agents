# database_mgmt scripts

Postgres backup and restore helpers that execute **`pg_dump`** / **`psql`** **inside** the Compose **`db`** service via **`docker compose exec`**. This avoids host/client PostgreSQL version mismatches that break dumps when developers run mismatched local **`pg_dump`** binaries.

Both scripts read **`DB_*`** settings from **`packages.config`** — the same single source of truth as application code and **`scripts/backup_db.sh`**.

## Prerequisites

- Docker Compose platform stack running (**`db`** service healthy)
- Invoked from **`agent_fleet/`** so **`docker compose`** resolves **`docker-compose.yml`**
- Write access to **`agent_fleet/db_backups/`** (created on demand for backups)

## Scripts

### backup_db.sh

1. Ensures **`db_backups/`** exists under **`agent_fleet/`**
2. Runs **`pg_dump`** inside the **`db`** container for **`$DB_NAME`**
3. Writes a timestamped **`.sql`** file into **`db_backups/`**

Use before schema migrations, destructive experiments, or refreshing a shared dev database snapshot.

### restore_db.sh

1. Takes a path to a **`.sql`** dump (typically under **`db_backups/`**)
2. Replays the script into the running **`db`** container via **`psql`**

**Warning:** restore overwrites data in the target database. Stop dependent services or expect connection errors during replay.

## Comparison with `scripts/backup_db.sh`

| Approach | When to use |
|----------|-------------|
| **`database_mgmt/backup_db.sh`** | Postgres runs in Compose; prefer exec-in-container |
| **`scripts/backup_db.sh`** | Host **`pg_dump`** can reach the DB with compatible versions |

For local silicon development, **`database_mgmt/`** is usually the less fragile choice.

## Configuration surface

Connection parameters come from **`packages.config`** (environment variables documented in **`.env.example`** at repo root). Do not hardcode credentials in these shell scripts.

Secrets belong in **`.env`**, not in git-tracked backup files.

## Operational notes

- Dumps in **`db_backups/`** are **artifacts**, not source — do not commit them.
- Large databases may need disk space on the Docker volume and host bind mount.
- Restoring does not automatically restart fleet-server or agents; restart Compose services if connections pool stale credentials or schemas.

## Related

| Document | Topic |
|----------|--------|
| [`../README.md`](../README.md) | Scripts index |
| [`../../docs/RUN.md`](../../docs/RUN.md) | Platform bring-up |
| [`../../deploy/README.md`](../../deploy/README.md) | Non-secret service config mounts |

## Example invocations

From **`agent_fleet/`** with platform Compose up:

```bash
./scripts/database_mgmt/backup_db.sh
./scripts/database_mgmt/restore_db.sh db_backups/your_dump.sql
```

Verify connectivity first:

```bash
docker compose ps db
docker compose exec db pg_isready
```

If restore fails mid-file, treat the database as inconsistent — take a fresh backup before retrying, or recreate the volume and replay from a known-good dump.

## Security notes

- Backup files may contain fleet metadata and task history — store them like production data.
- Never commit **`db_backups/*.sql`** to git (should stay gitignored).
- Rotating **`DB_PASSWORD`** requires updating **`.env`** and restarting **`db`** plus dependents, then taking a new baseline backup.
