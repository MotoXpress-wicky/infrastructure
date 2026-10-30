# Smoke test

One Python file, no packages to install. It uses the real HTTP API of a **running** stack and walks through a
whole shop day: first admin, register, emails, password reset, a part with a photo, an order, shipping, delivery,
cash collection, a courier receipt, a cancelled order, a returned parcel, and the access rules.

```bash
cd infrastructure
docker compose -f environments/local/docker-compose.yml up -d     # wait until the services are healthy
python tests/smoke.py
```

Every run uses new names, so you can run it again and again. Exit code `0` means everything passed.
It needs the local env file `environments/local/env/user-service.env` (it reads the first admin from it).

## What it proves

| Part | Checked through |
|---|---|
| Events between services | user -> notification (emails), order <-> payment (payment status) |
| Emails | Mailpit (`http://mail.localhost`) |
| Photos and files | object storage, and `/media/...` through Nginx |
| Login and roles | 401 without login, 403 for a customer, 200 for an admin |

## Outage check (by hand, about 2 minutes)

The smoke test cannot stop RabbitMQ itself, so check the outbox (M46) like this:

1. `docker compose -f environments/local/docker-compose.yml stop rabbitmq`
2. Log in at http://localhost, put a part in the cart and place an order. **It must work** (a normal order page, maybe 2 seconds slower).
3. Open http://admin.localhost, **Payments**. The order has no payment yet. (The event waits in the table `outbox_events` of order-service.)
4. `docker compose -f environments/local/docker-compose.yml start rabbitmq`
5. Wait up to about 30 seconds and reload **Payments**. The payment is there, `PENDING`, and the confirmation email is in http://mail.localhost.

On the real jars with a stand-in broker this gave: checkout 201 in 1.7 s while the broker was down, and the payment and the email about 10 seconds after the broker came back, with no second payment.

## Settings (all optional)

| Name | Meaning |
|---|---|
| `SMOKE_BASE_URL` | The customer site. Default `http://localhost` (every API is reachable there) |
| `SMOKE_USER_URL`, `SMOKE_PRODUCT_URL`, `SMOKE_ORDER_URL`, `SMOKE_PAYMENT_URL` | One service somewhere else, for example `http://localhost:8081` when you run it in IntelliJ without Nginx |
| `SMOKE_MAIL_FILE` | A `.jsonl` file of mails instead of Mailpit |
| `SMOKE_SKIP_MEDIA=1` | Do not fetch the photo through `/media` |
| `SMOKE_WAIT_SECONDS` | How long to wait for an event, default 40 |

## What was checked and what was not (2026-10-30)

The whole script passed 36 of 36 against the real service jars, real PostgreSQL 17 and a real AMQP broker (Apache
Qpid Broker-J as a stand-in), with a small fake S3 and a fake SMTP server. Docker was not available.

**Not checked yet, because Docker was off:**
- real RabbitMQ and its **dead-letter queues** (Qpid does not know the `x-dead-letter-*` queue arguments);
- real SeaweedFS (bucket rules, public `/media` through Nginx);
- the Mailpit REST API calls in this script (they follow Mailpit's documented `/api/v1/messages` and
  `/api/v1/message/{id}`; the rest of the script ran with the file option instead);
- the Docker images themselves.

If one of these fails on your machine, the message after `->` shows what the service answered.
