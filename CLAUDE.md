# motoXpress — context for Claude

**First, read `docs/session-handoff.md`.** It says what is done, what is not done,
and what to do next. Do not change anything until you have read it and told me your plan.

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
- Never put real secrets in a committed file. Real values go in a local `.env` file only.
- The repos on GitHub are public.

## Facts and code
- Never invent class names, annotations, config properties, Maven coordinates, or versions.
  If unsure, say so and name the official doc page.
- Use the versions in each pom.xml / package.json.
- If there are 2+ correct ways, show a small comparison table, pick one, say why.

## Folder layout
motoxpress/
  infrastructure/  user-service/  product-service/  order-service/
  notification-service/  recommendation-service/  users-ui/  admin-ui/
Each is a separate git repo. The parent folder is not a repo.
A cloud session only sees the repo it is attached to.

## Stack
Java 21, Spring Boot, Maven, PostgreSQL, Flyway, Redis, RabbitMQ, Docker, Nginx,
GitHub Actions, Kubernetes + ArgoCD + Kustomize, Terraform. UIs: Vite + React + TypeScript.

## Project rules
- One service = one job = one database. A service never reads another service's tables.
- user-service and notification-service must stay domain-free. The words order, product,
  part, vehicle, cart, motoXpress must never appear in their code. Reuse by config only.
- Anything that can change between projects goes in application.yaml, never in Java.
- All API paths: /api/v1/<service>/...
- Production grade = input validation, one shared error JSON, logs with trace id, tests,
  profiles (dev/docker/prod), health checks, no secrets in git.
- No admin-service. Admins are users with ROLE_ADMIN in user-service.

## Local development
- infrastructure/local/docker-compose.yml starts ONLY helpers:
  PostgreSQL, Redis, RabbitMQ, Nginx. It never starts the services.
- I start Java services in IntelliJ and UIs with "npm run dev" myself.
- Nginx reaches them through host.docker.internal.

| Thing | Port |
|---|---|
| Nginx customer site / admin site | 80 / 8000 |
| users-ui / admin-ui | 3000 / 3001 |
| user / product / order / notification / suggestion service | 8080 / 8081 / 8082 / 8083 / 8084 |
| PostgreSQL / Redis / RabbitMQ / RabbitMQ UI | 5432 / 6379 / 5672 / 15672 |

The names "suggestion" and "recommendation" are not settled. See
`docs/session-handoff.md`, section 6, problem 1.

## Where to read more
- Handoff and next steps: `docs/session-handoff.md`
- Decisions: `docs/architecture/decisions.md`
- Event rules: `docs/architecture/06-event-contracts.md`
