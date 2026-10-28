# Home-server deployment

This fork packages OpenCVE v3.1.0 as registry-first webserver and Airflow
images. The public application binds only to the LAN address on port `8092`;
the Airflow administration UI stays on loopback port `8093`.

## Prepare

```bash
cd docker
./install.sh -r v3.1.0 prepare
python3 prepare-home-server.py
```

The generated `docker/.env` and Django configuration are ignored by Git. The
preparation script creates unique PostgreSQL, Airflow and Django secrets and
does not print them. It refuses to overwrite an existing home-server
configuration because rotating only the files would disconnect the existing
PostgreSQL volume. `--force` is reserved for a planned, database-aware
credential rotation.

## Start

After the GHCR images have been published from `master`:

```bash
docker compose pull
./install.sh init-docker-stack
./install.sh clone-repositories
./install.sh import-opencve-kb
./install.sh start-opencve-dag
```

Create the first OpenCVE administrator separately with
`./install.sh create-superuser` from an interactive local shell.

OpenCVE: `http://192.168.178.57:8092`

## Watchtower

The stateless application containers are registered with Watchtower in
monitor-only mode. Airflow upgrades must pause active DAGs and migrate the
stack in a controlled order, so Watchtower must not replace those containers
mid-task. Nginx is the only automatically replaced service. PostgreSQL and
Redis are deliberately excluded. The webserver entrypoint still applies
idempotent Django migrations and refreshes static files before accepting
traffic. New application images are published only after changes reach the
fork's `master` branch.

## Backup

Before application upgrades:

```bash
docker compose exec -T postgres pg_dump -U opencve opencve | gzip > "opencve-backup-$(date +%Y%m%d).sql.gz"
```

Do not run `./install.sh reset`: it removes the persistent database and
repository volumes.
