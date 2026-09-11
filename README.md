# motoXpress — infrastructure

## 1. What this repo is

| Folder | Job |
|---|---|
| `local/` | Docker Compose for local helpers: PostgreSQL, Redis, RabbitMQ, Nginx. |
| `k8s/` | Kubernetes files for ArgoCD. Still empty. |
| `terraform/` | Cloud resources. Still empty. |

This repo never starts the Java services or the UIs. You start those yourself.

## 2. Required folder layout

All repos sit side by side in one parent folder:

```
motoxpress/
  infrastructure/
  user-service/
  product-service/
  order-service/
  notification-service/
  product-suggestion-service/
  users-ui/
  admin-ui/
```

The parent folder is not a git repo. Each folder is its own repo.

## 3. First-time setup

1. Open a terminal in this repo.
2. Go to the local folder: `cd local`
3. Copy the example file:
   - Bash: `cp .env.example .env`
   - PowerShell: `Copy-Item .env.example .env`
4. Open `.env` and put real values. Never commit this file.
5. Start the helpers: `docker compose up -d`
6. Start the Java services in IntelliJ.
7. Start each UI with `npm run dev`.

## 4. Daily commands

Run these inside the `local/` folder.

| Goal | Command |
|---|---|
| Start | `docker compose up -d` |
| Stop | `docker compose down` |
| Status | `docker compose ps` |
| Logs | `docker compose logs -f postgres` |

## 5. Connect a service to the helpers

| Helper | Host | Port |
|---|---|---|
| PostgreSQL | localhost | 5432 |
| Redis | localhost | 6379 |
| RabbitMQ | localhost | 5672 |

Each service uses its own database and DB user, for example `user_db` and `user_service`.

## 6. URLs

| Page | URL |
|---|---|
| Customer site | http://localhost |
| Admin site | http://localhost:8000 |
| RabbitMQ UI | http://localhost:15672 |

## 7. Reset all local data

```
docker compose down -v
```

WARNING: this deletes all databases and all local data.

## 8. Problems

| You see | Meaning and fix |
|---|---|
| 502 Bad Gateway | Nginx works, but nothing runs on that port. Start the service. |
| 404 page that says "nginx" | No `location` matches the path. Check `local/nginx/default.conf`. |
| 404 JSON from Spring | Nginx worked; the service has no such endpoint. |
| "port is already allocated" | Another program uses that port. Stop it, then try again. |
