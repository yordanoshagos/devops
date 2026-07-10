# Decoy repo — pull your MELT share

This copy lives at **https://github.com/yordanoshagos/devops.git** so each
person can clone, check out their branch, and push their slice without touching
the real `devops-satellite-telemetry` repo until review is done.

## Clone once

```bash
git clone https://github.com/yordanoshagos/devops.git
cd devops
git fetch origin
```

## Pick your branch

| You | Branch | Your files (author) |
|-----|--------|---------------------|
| **Yordanos** | `feature/obs-service-a` | `service-a/**`, `jaeger/README.md`, `docs/architecture.md` |
| **Saloi** | `feature/obs-service-b` | `service-b/**`, `prometheus.yml`, `alert-rules.yml`, `.github/workflows/container-ci-cd.yml` |
| **Berissa** | `feature/obs-service-c` | `service-c/**`, `scripts/load-test.*`, `scripts/simulate-failure.sh`, `docs/benchmark-report.md`, `docker-compose.prod.yml` |
| **Arsema** | `feature/obs-compose-grafana` | `docker-compose.yml`, `grafana/**`, `loki/**`, `promtail/**`, `alertmanager/**`, README observability section, `docs/observability-work-split.md` |

```bash
git checkout feature/obs-service-b   # example for Saloi
```

The branch contains the **full** stack (everyone needs it to run `docker compose up`).
Only edit **your** files above; open a PR into `develop` when ready.

## Branches on this remote

| Branch | Purpose |
|--------|---------|
| `main` | Updated baseline (same as latest `develop`) |
| `develop` | Integration branch — all MELT work merged here |
| `feature/obs-service-a` … `feature/obs-compose-grafana` | Per-person working branches |

## Review cycle (same as real repo)

Yordanos → Saloi → Arsema → Berissa → Yordanos (each reviews exactly one PR).

Full file list and debugging notes: [`docs/observability-work-split.md`](docs/observability-work-split.md).

## Quick verify after pull

```bash
docker compose up --build -d
curl http://localhost/health
open http://localhost:3000    # Grafana admin/admin
open http://localhost:16686   # Jaeger
```
