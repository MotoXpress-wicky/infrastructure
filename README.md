# motoXpress — infrastructure

## 1. What this repo is

| Folder | Job |
|---|---|
| `environments/local/` | The whole system on **your PC**: `docker-compose.yml` (helpers + every service), Nginx, Postgres init, `env/` (one settings file per container) |
| `environments/staging/` | The same for the **staging server** (a VPS, later) |
| `.github/workflows/release-service.yml` | **Shared pipeline** every service repo calls: build the image, write its tag into an environment's `docker-compose.yml` |
| `.github/workflows/check-compose.yml` | Checks both environments on every pull request and push |
| `docs/` | Architecture. Start with [docs/mvp/README.md](docs/mvp/README.md). |

## 2. How a new version reaches an environment

```
service repo (e.g. order-service): push to main
  → its CI runs the tests
  → its CD calls release-service.yml:
       build image ghcr.io/motoxpress-wicky/order-service:<commit id>, push it
       write that tag into environments/local/docker-compose.yml, commit to this repo
you:   git pull  →  cd environments/local  →  docker compose pull && docker compose up -d

staging: in the service repo, "Run workflow" (CD) → the same tag goes into
         environments/staging/docker-compose.yml
```

The image tags in the compose files are **written by the pipelines**. Do not edit them by hand.

## 3. Required folder layout

```
motoxpress/
  infrastructure/
  user-service/
  product-service/
  order-service/
  notification-service/
  payment-service/         (create this repo when you build it)
  users-ui/
  admin-ui/
```

The parent folder is not a git repo. Each folder is its own repo.

## 4. First-time setup (your PC)

1. `cd environments/local`
2. The env files in `env/` are already in git, with values that work only on your PC.
   You do not need to change them. Values that two containers share already match.
3. Optional, only for Google login, real email and push. These are real secrets, ignored by git:
   - copy `env/user-service.secrets.env.example` to `env/user-service.secrets.env` and fill in your
     Google and Gmail values (it overrides the placeholders in `user-service.env`);
   - download the Firebase key into `env/firebase.json`. Do this **before** you start
     notification-service, or Docker creates an empty folder with that name.
4. Log in to GitHub Container Registry, if the images are private. You need a GitHub token
   that can read packages (GitHub docs: "Working with the Container registry"):
   `docker login ghcr.io`
5. Start: `docker compose up -d`

Until a service has its first image (its tag still says `not-built-yet`), start only what exists:
`docker compose up -d postgres redis rabbitmq object-storage mailpit nginx`

## 5. Work on one service in IntelliJ

1. `docker compose stop order-service`
2. Run order-service in IntelliJ (port 8082), or `npm run dev` for a UI.
3. Nothing else to change. Nginx tries the container, sees it is stopped, and sends the
   request to your IntelliJ copy.
4. When done: stop it in IntelliJ, then `docker compose start order-service`.

Your IntelliJ copy reaches the helpers on `localhost` (see section 7). Service containers have no
published ports, so it cannot call another service's container; run that service in IntelliJ too.

## 6. Daily commands (inside `environments/local`)

| Goal | Command |
|---|---|
| Get new versions | `git pull`, then `docker compose pull && docker compose up -d` |
| Start | `docker compose up -d` |
| Stop | `docker compose down` |
| Status | `docker compose ps` |
| Logs | `docker compose logs -f order-service` |

## 7. Addresses (your PC)

| Page | URL |
|---|---|
| Customer site | http://localhost |
| Admin site | http://admin.localhost |
| RabbitMQ UI | http://rabbitmq.localhost |
| Mailpit inbox | http://mail.localhost |
| A product photo / a profile picture | http://localhost/media/products/&lt;key&gt; / http://localhost/media/avatars/&lt;key&gt; |

| Helper (for IntelliJ) | Host and port |
|---|---|
| PostgreSQL / Redis / RabbitMQ | localhost 5432 / 6379 / 5672 |
| Object storage (S3 API) / Mailpit SMTP | localhost 8333 / 1025 |

Only port 80 (Nginx) is open to your network. The helper ports are bound to `127.0.0.1` (this PC only).

## 8. Reset all local data

```
docker compose down -v
```

WARNING: this deletes all databases, all queued messages and all stored photos and PDFs.
You need it once after the database list changes, because the init SQL runs only on an empty volume.

## 9. Problems

| You see | Meaning and fix |
|---|---|
| 502 Bad Gateway | Neither the container nor an IntelliJ copy runs for that path. Start one. |
| `not-built-yet: not found` when starting | That service has no image yet. Start only the parts that exist (section 4). |
| `object-storage` stays unhealthy | Read `docker compose logs object-storage`. Usually a key pair is missing in `env/object-storage.env`. |
| `env file ... not found` | An env file is missing in `env/`. Local: run `git pull`. Staging: create it from its `.example`. |
| Google login or email fails locally | `env/user-service.secrets.env` is missing or empty (section 4, step 3). |
| 404 page that says "nginx" | No `location` matches the path. Check `nginx/api-routes.inc`. |
| 404 JSON from Spring | Nginx worked; the service has no such endpoint. |
| A photo URL answers 403 or 404 | The key is wrong, or the file is in a private bucket (never public). Check `object-storage/buckets.conf`. |
| "port is already allocated" | Another program uses that port. Stop it. |
| `admin.localhost` not found in a terminal tool | Browsers resolve `*.localhost` by themselves. For other tools, add the name to the hosts file. |
| `Detect hardcoded secrets ... Failed` when you commit | gitleaks found a secret in your staged changes. Remove it (move it to an ignored env file), then commit again. |

## 10. Secret check before every commit (all repos)

Every motoXpress repo has a `.pre-commit-config.yaml`. It runs **gitleaks** (a secret scanner)
through **pre-commit** (a tool that runs checks before `git commit`). A commit with a secret is blocked.

1. Install pre-commit once per PC: `pip install pre-commit`
2. Turn it on once per clone, inside each repo: `pre-commit install`
3. Check: `pre-commit run`. You should see `Detect hardcoded secrets....Passed`.

The first run builds gitleaks with Go (pre-commit downloads Go if it is missing), so it takes a minute.
The hook checks only new staged changes, not old history. `git commit --no-verify` skips it: never do that.
