# motoXpress — context for Claude

**First, read `docs/mvp/README.md`.** It is the design of what we build now.
`docs/session-handoff.md` is an older snapshot (2026-10-19); the MVP docs replace its design parts.
Do not change anything until you have read the MVP docs and told me your plan.

This file is a copy of my root `CLAUDE.md`. The root folder is not a git repo,
so a cloud session cannot see it. Keep the two files the same.

## About me
- University student. I know basic Java. I am a complete beginner in Spring and Spring Boot.
- English is not my first language. Use simple words and short sentences. One idea per sentence.
- No idioms or slang. Explain every technical word in one line the first time.
- Prefer numbered steps and small tables over long paragraphs.

## How to teach me
- Explain WHY in one or two lines, then HOW.
- For every code change: say the file, its folder, and the meaning of each annotation.
- Smallest working version first. Extra features after it runs.
- After each step: give the exact command or URL to check it, and the output I should see.
- When I paste an error: explain what it means first, then fix it.
- If my idea is bad, say so plainly and give the better option with the reason.
- Ask before running any command that changes things (git push, docker compose down -v, deleting files).

## Git rules
- Do not commit or push unless I ask. I usually commit myself.
- Do not add a `Co-Authored-By` line to commits. My commits must show only my name.
- Never print passwords or secrets in chat.
- Never put real secrets in a committed file. Staging values go only in `environments/staging/env/*.env` (ignored by git).
- Local env files (`environments/local/env/*.env`) are committed with local-only values. The real
  Google, Gmail and Firebase secrets go only in `env/user-service.secrets.env` and `env/firebase.json` (ignored).
- The repos on GitHub are public.

## Facts and code
- Never invent class names, annotations, config properties, Maven coordinates, or versions.
  If unsure, say so and name the official doc page.
- Use the versions in each pom.xml / package.json.
- If there are 2+ correct ways, show a small comparison table, pick one, say why.

## Folder layout
motoxpress/
  infrastructure/  user-service/  product-service/  order-service/
  notification-service/  payment-service/  users-ui/  admin-ui/
Each is a separate git repo. The parent folder is not a repo.
A cloud session only sees the repo it is attached to.
recommendation-service is not part of the MVP.

## Stack
Java 21, Spring Boot, Maven, PostgreSQL, Flyway, Redis, RabbitMQ, Docker, Nginx,
GitHub Actions. UIs: Vite + React + TypeScript.
Environments: Docker Compose everywhere. infrastructure/environments/local (my PC) and
infrastructure/environments/staging (a VPS later). Images in GitHub Container Registry, built by CI
from main. Kubernetes is a "maybe later", not part of the MVP.

## Project rules
- One service = one job = one database. A service never reads another service's tables.
- user-service and notification-service must stay domain-free. The words order, product,
  part, vehicle, cart, motoXpress must never appear in their code. Reuse by config only.
- Anything that can change between projects goes in application.yaml, never in Java.
- All API paths: /api/v1/<service>/...
- Production grade = input validation, one shared error JSON, logs with trace id, tests,
  profiles (dev/docker/prod), health checks, no secrets in git.
- No admin-service. Admins are users with ROLE_ADMIN in user-service.
- Cash on delivery only in the MVP. Couriers deliver; admins enter tracking numbers and courier receipts.

## Local development
- infrastructure/environments/local/docker-compose.yml holds ALL helpers and ALL services.
  `docker compose up -d` starts everything from the CI-built images.
- Each service's image tag in that file is written by its pipeline (shared workflow
  infrastructure/.github/workflows/release-service.yml). Never edit the tags by hand.
- To work on one service: `docker compose stop <service>`, run it in IntelliJ (or `npm run dev`).
  Nginx tries the container first and falls back to host.docker.internal by itself.
- environments/staging/ is the same for the staging VPS (later); its tags come from a
  "promote to staging" run of each service's pipeline.

| Thing | Address / port |
|---|---|
| Customer site / admin site (Nginx) | http://localhost / http://admin.localhost (both port 80) |
| users-ui / admin-ui (Vite) | 3000 / 3001 |
| user / product / order / notification / payment service | 8080 / 8081 / 8082 / 8083 / 8084 (inside Docker only; IntelliJ copies use the same ports) |
| PostgreSQL / Redis / RabbitMQ / object storage S3 / Mailpit SMTP | 5432 / 6379 / 5672 / 8333 / 1025 (on 127.0.0.1, for IntelliJ) |
| RabbitMQ UI / Mailpit inbox | http://rabbitmq.localhost / http://mail.localhost |

Object storage: SeaweedFS container `object-storage`, S3 API. It creates its own buckets on start
(environments/<env>/object-storage/buckets.conf) and one S3 user per service (users.conf).
Buckets: product-media and user-avatars (public, /media/products/ and /media/avatars/),
courier-receipts and shipment-documents (private). Store only object keys in databases.

## Where to read more
- MVP design: `docs/mvp/README.md`
- MVP decisions: `docs/mvp/decisions.md`
- Event rules: `docs/architecture/06-event-contracts.md` (MVP subset: `docs/mvp/07-events.md`)
