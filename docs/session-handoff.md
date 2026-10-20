# motoXpress — session handoff

> **Out of date (design parts).** Since this was written, the MVP design was finished in
> [mvp/README.md](mvp/README.md): cash on delivery, payment-service on 8084, no recommendation-service,
> admin site at `admin.localhost`, servers on a VPS with Docker Compose (no Kubernetes, no Terraform).
> Read the MVP docs first. Sections 1 (how to teach me) and the git rules below still apply.

Written on 2026-10-19. Read this file first. It tells a new Claude session
what the project is, what is done, what is not done, and what to do next.

Facts below were checked on disk on this date. Anything not checked is marked
**UNVERIFIED**. Do not trust an UNVERIFIED line. Check it first.

---

## 1. Who I am and how to teach me

- University student. I know basic Java. I am a complete beginner in Spring and Spring Boot.
- English is not my first language. Use simple words and short sentences. One idea per sentence.
- No idioms or slang. Explain each technical word in one line the first time.
- Prefer numbered steps and small tables over long paragraphs.
- Explain WHY in one or two lines, then HOW.
- For every code change: say the file, its folder, and the meaning of each annotation.
- Smallest working version first. Extra features after it runs.
- After each step: give the exact command or URL to check it, and the output I should see.
- When I paste an error: explain what it means first, then fix it.
- If my idea is bad, say so plainly and give the better option with the reason.
- Never invent class names, annotations, config properties, Maven coordinates, or versions.
  If unsure, say so and name the official doc page.
- If there are 2 or more correct ways, show a small comparison table, pick one, say why.

### Git rules (important)

- **Do not commit or push unless I ask.** I usually commit myself.
- Ask before any command that changes things: `git push`, `docker compose down -v`, deleting files.
- Never print passwords or secrets in chat.
- Never put real secrets in a committed file. Real values go in a local `.env` file only.
- Do **not** add a `Co-Authored-By` line to commits. I decided this on 2026-10-19: no trailer.
  My commits must show only my name.

---

## 2. The project

motoXpress is a vehicle part ordering system. It is a Spring Boot microservice system.

Stack: Java 21, Spring Boot (version 4.1.1 in `user-service/pom.xml`), Maven, PostgreSQL,
Flyway, Redis, RabbitMQ, Docker, Nginx, GitHub Actions, Kubernetes + ArgoCD + Kustomize,
Terraform. UIs: Vite + React + TypeScript.

### Folder layout

All repos sit side by side. **Each folder is its own git repo. The parent folder is NOT a repo.**

```
motoxpress/
  CLAUDE.md                 <- root file, not in any repo
  infrastructure/  user-service/  product-service/  order-service/
  notification-service/  recommendation-service/  users-ui/  admin-ui/
```

A cloud session only sees the repo it is attached to. It cannot see the root
`CLAUDE.md`. That is why section 1 above repeats the rules.

### Ports

| Thing | Port |
|---|---|
| Nginx customer site / admin site | 80 / 8000 |
| users-ui / admin-ui | 3000 / 3001 |
| user / product / order / notification / suggestion service | 8080 / 8081 / 8082 / 8083 / 8084 |
| PostgreSQL / Redis / RabbitMQ / RabbitMQ UI | 5432 / 6379 / 5672 / 15672 |

Decision 33 gives recommendation-service port 8085. See section 6, problem 1.

### Project rules

1. One service = one job = one database. A service never reads another service's tables.
2. user-service and notification-service must stay domain-free. The words order, product,
   part, vehicle, cart, motoXpress must never appear in their code. Reuse by config only.
3. Anything that can change between projects goes in `application.yaml`, never in Java.
4. All API paths: `/api/v1/<service>/...`
5. Production grade = input validation, one shared error JSON, logs with trace id, tests,
   profiles (dev/docker/prod), health checks, no secrets in git.
6. No admin-service. Admins are users with `ROLE_ADMIN` in user-service.

### Local development model

- `infrastructure/local/docker-compose.yml` starts ONLY helpers: PostgreSQL, Redis, RabbitMQ, Nginx.
  It never starts the services.
- I start Java services in IntelliJ and UIs with `npm run dev`.
- Nginx reaches them through `host.docker.internal`.
- Browser opens `http://localhost` (customer) or `http://localhost:8000` (admin).
  One origin, so no CORS and cookies just work.

---

## 3. What is DONE

### 3.1 infrastructure repo (branch `main`, clean, up to date with GitHub)

| Item | State |
|---|---|
| `local/docker-compose.yml` | Done. postgres:17-alpine, redis:8-alpine, rabbitmq:4.3-management, nginx:stable. Ports bound to 127.0.0.1 except Nginx. |
| `local/.env.example` | Done. Placeholders only. |
| `local/postgres/init/01-create-databases.sh` | Done. Creates 5 databases and 5 DB users. `REVOKE CONNECT ... FROM PUBLIC` stops cross-service access. |
| `local/nginx/default.conf` | Done. Two server blocks (80 customer, 8000 admin). Uses `X-Forwarded-For $remote_addr` (overwrite, not append, so a client cannot fake its IP). |
| `README.md` | Done. |
| `k8s/`, `terraform/` | Empty folders with `.gitkeep` only. Intentional. |
| `docs/architecture/` | Done: `01-context-diagram`, `02-container-diagram`, `03-component-diagram` (user-service), `06-event-contracts`, `decisions` (28 rows), `README`. |

### 3.2 user-service repo (branch `main`)

Done and committed (last commit: "removed docker compose file, created universal error response"):

| Item | State |
|---|---|
| One shared error JSON | `ErrorResponse` record, 7 fields: `timestamp, status, code, message, path, refreshable, details`. Every handler, the JWT entry point and the rate-limit filter use it. |
| One error code enum | `exception/ErrorCode.java`. `refreshable` is true only for `ACCESS_TOKEN_EXPIRED`. Other values use a short constructor that sets false. |
| Old classes removed | `AuthErrorCode`, `AuthErrorResponse` deleted. |
| No message leak | `GlobalExceptionHandler` no longer sends `exception.getMessage()` on a crash. |
| New paths | `/api/v1/user/auth/...` and `/api/v1/user/profile`. Cookie path changed too. |
| Config fixes | Access token TTL 15 minutes (was 1). `rate-limit.trust-proxy-headers: true`. Frontend and CORS URLs point at `http://localhost`. |
| `ClientIpResolver` | Now used by `RateLimitFilter` and `AuthController` (captcha). The copy-pasted IP code is gone. |
| RestClient | `spring-boot-starter-restclient` is in `pom.xml` (about line 63). Spring Boot 4 does not create a `RestClient.Builder` without it. |
| Tests | On 2026-09-11 all 48 tests passed. **UNVERIFIED since then. Re-run `./mvnw test`.** |

One uncommitted change: a comment line in `application.yaml`.

### 3.3 users-ui repo (branch `main`, clean)

| Item | State |
|---|---|
| All API calls | Use `/api/v1/user/...`. |
| `axiosClient` | `baseURL` is empty (same origin, through Nginx). |
| `vite.config.ts` | Port 3000. |
| Types | `ErrorCode` and `ApiErrorBody` in `auth.types.ts`. `getErrorCode()` helper in `getErrorMessage.ts`. |
| Google button | Uses same origin. |
| Checks | **UNVERIFIED.** `npm install` and `npx tsc -b` were never run by Claude. `node_modules` did not exist. |
| `.env.example` | **Not present now.** The UI needs `VITE_TURNSTILE_SITE_KEY` (public key) and optional `VITE_API_BASE_URL` (leave empty). |

### 3.4 Event contract (`06-event-contracts.md`)

- Exchange `app.events`, type `topic`, durable. Queue and binding are declared by the consumer only.
- Event names are past-tense facts in the publisher's words. A bound name is never renamed.
- Every message has a `messageId` header (UUID).
- 14 events: `user.registered`, `user.password.reset`, `user.password.changed`,
  `order.placed`, `order.paid`, `order.shipped`, `order.cancelled`, `order.refunded`,
  `payment.succeeded`, `payment.failed`, `payment.refunded`,
  `product.created`, `product.updated`, `product.deleted`.
- Note: `order.completed` was renamed to `order.paid` on 2026-09-17, before anything bound to it.

---

## 4. What is NOT done

| # | Item | Note |
|---|---|---|
| 1 | **The helpers have never been started.** | `infrastructure/local/.env` does not exist. On 2026-10-19 Docker Desktop was not running. |
| 2 | Flyway | Not in `user-service/pom.xml`. `ddl-auto: update` is still set. |
| 3 | JWT secret | Config reads `${JWT_SECRET}`. But the repo is public and **the old real secret is still in git history**. It must be replaced with a new secret. Only I do this. Never ask me to paste it. |
| 4 | user-service publishes no events yet | The contract exists. No RabbitMQ code. |
| 5 | Other services | `product-service`, `order-service`, `notification-service`, `recommendation-service`, `admin-ui` are empty folders. `payment-service` has no folder. |
| 6 | End-to-end test | Nobody has yet opened `http://localhost` and logged in through Nginx. |

---

## 5. user-service `.env` (local run)

Put these in `user-service/.env` (it is read by `DotenvConfig`). Never commit it.

| Variable | Value |
|---|---|
| `DB_URL` | `jdbc:postgresql://localhost:5432/user_db` |
| `POSTGRES_USER` | `user_service` |
| `POSTGRES_PASSWORD` | copy `USER_DB_PASSWORD` from `infrastructure/local/.env` |
| `REDIS_HOST` / `REDIS_PORT` | `localhost` / `6379` |
| `REDIS_PASSWORD` | copy `REDIS_PASSWORD` from `infrastructure/local/.env` |
| `JWT_SECRET` | a NEW random secret, at least 32 bytes |
| `MAIL_USERNAME`, `MAIL_APP_PASSWORD` | Gmail address and app password |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | from Google Cloud console |
| `TURNSTILE_SECRET_KEY` | from Cloudflare |

---

## 6. Problems and gaps found (decide these early)

| # | Problem | Evidence |
|---|---|---|
| 1 | **Service names do not match.** Root `CLAUDE.md`, the Nginx route `/api/v1/suggestion/` (port 8084) and `k8s/apps/product-suggestion-service/` say "suggestion". The decisions, the diagrams and the folder on disk say `recommendation-service` (Python, port 8085). | `decisions.md` row 33; `ls` of the root folder. |
| 2 | **payment-service is missing from the setup.** The container diagram has it and Nginx should route to it. But there is no Nginx route, no port, no `payment_db`, no k8s folder. | `default.conf` has no payment route. The init script creates `suggestion_db`, not `payment_db` or `recommendation_db`. |
| 3 | **Mailpit is missing.** Decision 16 says Mailpit locally. It is not in `docker-compose.yml`. | grep found 0 matches. |
| 4 | **Stale docs.** `decisions.md` says "events vs HTTP is not decided yet". It is decided. Root `CLAUDE.md` says "See infrastructure/docs/architecture.md" (file does not exist) and lists the path change as an open problem (it is done). | |
| 5 | **The event contract links to `claude/rabbitmq-notes.md`.** That file does not exist. | `find` found nothing on 2026-09-17 and on 2026-10-19. |
| 6 | **No copy of `CLAUDE.md` inside a repo.** The root folder has no git backup. The copy at `infrastructure/docs/CLAUDE.md` is gone. | |
| 7 | **Domain-free rule vs bindings.** notification-service binds to keys like `order.paid`. The rule says the word "order" must not be in its code. So binding keys and the event-to-template map must live in `application.yaml`. | Written in the container diagram, Legend 1. |
| 8 | **OAuth behind Nginx — UNVERIFIED.** Google sign-in builds its redirect URL from `{baseUrl}`. Behind a proxy Spring may need to trust the forwarded headers. I did not find a `forward-headers` setting in `application.yaml`. Check the Spring Boot reference, "Running behind a front-end proxy server". The Google console redirect URI must also be `http://localhost/login/oauth2/code/google`. | |
| 9 | **Push provider not chosen.** Queue `notification.push` exists in the contract. No outside system is drawn. | |

---

## 7. Proposed next steps (in order — I decide)

1. **Start the helpers (Part 3).** Ask me before each command.
   1. Start Docker Desktop.
   2. In `infrastructure/`: `git check-ignore -v local/.env` must show the file is ignored.
   3. Create `local/.env` with random strong passwords. Do not print them.
   4. Check ports 5432 and 6379 are free.
   5. In `infrastructure/local`: `docker compose config --quiet`, `docker compose up -d`, `docker compose ps`.
   6. `docker compose exec nginx nginx -t` must say "syntax is ok".
   7. `docker compose exec postgres psql -U postgres -c "\l"` must list the databases.
2. **Fix the naming and the gaps** (section 6, problems 1 to 4): one name for the recommendation service,
   add payment-service routes and databases, add Mailpit, update the stale docs.
3. **Run user-service end to end.** `./mvnw test`, start it in IntelliJ, `npm install` and `npm run dev` in
   users-ui, open `http://localhost`, register and log in. Check the Google login (problem 8).
4. **Flyway** for user-service, then `ddl-auto: validate`. Write the full SQL schema for the 4 entities.
5. **Rotate the JWT secret.**
6. **Publish user events** from user-service as the contract says. Keep it domain-free.
7. **Build notification-service** (domain-free; consumes `notification.email`; templates and bindings in config).
8. Then product-service, order-service, payment-service (cash on delivery first, OnePay second),
   recommendation-service (SQL-rule fallback first, LightFM later), admin-ui.

---

## 8. Where to read more

| Topic | File |
|---|---|
| Decisions and reasons | `infrastructure/docs/architecture/decisions.md` |
| Event rules | `infrastructure/docs/architecture/06-event-contracts.md` |
| Big picture | `infrastructure/docs/architecture/01-context-diagram.md`, `02-container-diagram.md` |
| user-service parts | `infrastructure/docs/architecture/03-component-diagram.md` |
| How to run local helpers | `infrastructure/README.md` |
