# MVP decisions

The MVP keeps the decisions in [../architecture/decisions.md](../architecture/decisions.md)
that still apply. This file lists what is new or different for the MVP.

## Kept from the full architecture

| # | Decision (short) |
|---|---|
| 2 | One service = one job = one database |
| 4 | Nginx is the gateway, routing only |
| 6 | One PostgreSQL server, one database and one DB user per service |
| 7 | No admin-service; admins are users with `ROLE_ADMIN` |
| 8 | First admin by bootstrap; other admins promoted, with an audit log |
| 12 | API paths `/api/v1/<service>/...` |
| 13 | On the laptop, Docker Compose runs only helpers; services and UIs run on the laptop |
| 16 | Email through SMTP; Mailpit on the laptop and the dev server |
| 36 | Stock is reserved over HTTP when an order is placed, released on cancel |
| 37 | The cart lives in the browser |

**Not in the MVP:** card payments and OnePay (18–24), refunds, recommendations (21, 27–33, 35),
Kubernetes, ArgoCD, Kustomize, Azure and Terraform (9–11, 14, 15). Their design stays in
`../architecture/` for later. Servers use a VPS with Docker Compose instead (M25).

## New for the MVP

| # | Decision | Reason | Status |
|---|---|---|---|
| M1 | Services: user, product, order, payment, notification. UIs: users-ui, admin-ui. | Smallest set that can sell parts | Accepted |
| M2 | **Cash on delivery only.** Card payments come when the business grows. | Start simple; most Sri Lankan online orders are cash on delivery | Accepted |
| M3 | payment-service is in the MVP. It owns payments and courier receipts. order-service keeps only a **copy** of the payment status, updated by events. | Money lives in one place; card payments later only add a new method (decision 19) | Accepted |
| M4 | An order has two status columns: `shipment_status` and `payment_status` | Cash is collected after the parcel moves; two small state machines are clearer than one | Accepted |
| M5 | Shipments are their own table in order-service. One shipment per order in the MVP. | No empty columns on the order; split deliveries possible later | Accepted |
| M6 | Courier companies deliver. No rider app. The admin enters the tracking number and marks delivered or returned by hand. | No staff riders while the business is small. A courier API can come later behind a `CourierGateway` interface | Accepted |
| M7 | Courier receipts are typed into the system with the PDF or photo as proof. They are matched to payments by **tracking number** and mark them PAID in one step. | Proof is kept; no loose paper; one place to update | Accepted |
| M8 | Payment statuses: `PENDING`, `COLLECTED`, `PAID`, `CANCELLED` | Plain words; `CANCELLED` covers "cancelled before shipping" and "returned" | Accepted |
| M9 | Push notifications through **Firebase Cloud Messaging**. notification-service sends both email and push. | Reaches the customer when the site is closed; also works for a phone app later | Accepted |
| M10 | Admin site on its own host name: `admin.localhost` now, `admin.<domain>` later | Separate cookies; easy to restrict later | Accepted |
| M11 | One codebase. Each environment is a folder in `infrastructure/environments/`: **local** (your PC) and **staging** (a VPS, later). Each folder has its own `docker-compose.yml` (helpers + every service), Nginx config, Postgres init and an `env/` folder with **one env file per container** (`user-service.env`, `postgres.env`, ...). All environments run the same images; only tags and secrets differ. | Build an image once, promote the same image; no copied code that drifts | Accepted |
| M12 | Login is required to buy. Browsing is public. | Orders, cancel and notifications need a known user | Proposed |
| M13 | A part has a unique part number, one category, fits zero or more bike models or is universal, has an optional part brand and a condition (New or Used) | Matches how riders search: by bike or by part number | Proposed |
| M14 | Nothing in the catalog is deleted; it is hidden | Old orders still point to it | Proposed |
| M15 | One flat delivery fee, set in order-service config | Simple; changes without code | Proposed |
| M16 | product-service publishes no events in the MVP | Nobody listens yet | Proposed |
| M17 | JWT signed with RS256. user-service has the private key; other services get the public key through config | Only user-service can create tokens (decision 3) | Proposed |
| M18 | Files live in **S3-compatible object storage** (SeaweedFS container, `object-storage`). Services use the standard AWS SDK S3 client; the address, keys and buckets come from env files. One bucket per purpose, owned by one service: `product-media` and `user-avatars` (public read, through Nginx `/media/products/` and `/media/avatars/`), `courier-receipts` and `shipment-documents` (private). Each service has its own S3 key, allowed only on its own bucket. The database stores only the **object key**; the API sends `MEDIA_BASE_URL + key`. | Browsers load photos directly, not through Java; moving to AWS S3 or a CDN changes only env files; private documents stay private | Accepted |
| M19 | Publish an event only after the database transaction commits. A reliable "outbox" comes later. | Never announce something that was rolled back | Proposed |
| M20 | All emails and push messages go through notification-service. Templates and the event → template map live in its config. | One place; stays domain-free | Accepted |
| M21 | The customer's "I received it" button is evidence only. It changes no status. | Only the courier receipt proves the money arrived | Proposed |
| M22 | No "confirmation call" status in the MVP | Add it only if fake orders become a problem | Proposed |
| M23 | When the admin marks a parcel returned, its stock reservation is released. The admin corrects stock by hand if the part came back damaged. | The part is back on the shelf | Proposed |
| M24 | `order.paid` is not published in the MVP | Nobody listens to it yet (no recommendations) | Proposed |
| M25 | Everything runs with **Docker Compose**, one complete `docker-compose.yml` per environment folder. Servers, when needed, are one VPS each. No Kubernetes, no Azure, no Terraform in the MVP. | Cheap and simple; one file shows the whole environment. Accepted risk: one machine per environment. | Accepted |
| M26 | HTTPS on servers with **Nginx + Certbot** (Let's Encrypt). Dev on your PC uses plain HTTP. | One web server tool everywhere | Accepted |
| M27 | Images in **GitHub Container Registry**, tagged with the git commit id | Part of GitHub; the workflow logs in with its own token; you always know which code runs | Accepted |
| M28 | Each service's pipeline writes its image tag **into the environment's `docker-compose.yml`** in the infrastructure repo. Push to `main` → new image + tag in `environments/local/`. "Run workflow" (promote) → that tag in `environments/staging/`. The steps live in one shared workflow, `.github/workflows/release-service.yml`, which every service repo calls. | Git shows what runs in each environment; rollback = the old tag; one pipeline to maintain, not seven | Accepted |
| M29 | On servers: nightly backup of every database and file volume, kept 14 days, **copied off the server** | The real server risk is losing data, not downtime | Accepted (tool: Open) |
| M30 | `k8s/` and `terraform/` folders removed | Not used with Docker Compose; git history keeps them | Accepted |
| M31 | Local Nginx tries each **container** first and falls back to the copy running in IntelliJ (`host.docker.internal`). To work on a service: `docker compose stop <service>`, run it in IntelliJ. Only Nginx serves the browser. Helper ports (PostgreSQL, Redis, RabbitMQ, Mailpit SMTP, object storage) are published on `127.0.0.1` so IntelliJ copies reach them; service ports are not published. | Whole system always running, with no config change to debug one service | Accepted |
| M32 | CI tests every push and pull request. Only a push to `main` builds an image and writes a tag. | Unfinished branches never reach any environment | Accepted |
| M33 | Each environment has one named Docker network (`motoxpress-local-network`, `motoxpress-staging-network`). Volumes only for data that must survive: PostgreSQL, RabbitMQ, object storage. | Clear, isolated environments; Redis only holds rate-limit counters | Accepted |
| M34 | The database init file is plain SQL (`01-create-databases.sql`). It reads passwords with psql's `\getenv`. | The Postgres container runs it natively; no shell, so Windows line endings cannot break it; passwords are safely quoted | Accepted |
| M36 | The object-storage container creates its own buckets and per-service users on every start (`object-storage/start.sh` + `buckets.conf` + `users.conf`, keys from `env/object-storage.env`). It strips Windows line endings itself. | No extra init container; buckets and access rules are a readable list; works the same on every machine | Accepted |
| M37 | Local env files are committed with readable local-only values (no `.example`). Turnstile uses Cloudflare's official test keys. Real third-party secrets (Google, Gmail, Firebase) stay in ignored files: `env/user-service.secrets.env` (loaded with `required: false`) and `env/firebase.json`. Staging keeps `.example` templates. | Clone and run with no setup; local passwords protect nothing outside your PC; the public repo still holds no real secret | Accepted |
| M38 | A failed event message is tried 3 times (2 s, then 4 s apart). After that it goes to a dead-letter queue named `<queue>.dlq`. A message that can never work (no `messageId`, no email address, unknown order) goes there at once. Every listener queue is declared with this rule. | Nothing loops forever, nothing is lost silently, and a person can look at the failed messages | Accepted |
| M39 | Until user-service signs tokens with RS256 (M17), product-service, order-service and notification-service check the login cookie with the **same `JWT_SECRET`** as user-service (HS256). | M17 is not built yet and the services must work now. Risk: any of these services could forge a token. Replace with the public key later. | Accepted (temporary) |
| M40 | "Delivered" and "returned" in bulk first check **every** shipment (nothing changes if one is wrong), then change each shipment in its own transaction and answer with `done` and `failed`. Shipments are chosen by id, not by tracking number. | A product-service outage during one return must not undo the other parcels; tracking numbers are unique only per courier | Accepted |
| M41 | order-service calls product-service to give stock back **inside** the transaction that locks the order row. If product-service is down the cancel or return fails and nothing changes. | A cancel and a new shipment can never cross each other; the person simply tries again | Accepted |
| M42 | payment-service stays domain-free: which event name starts which action (`CREATE`, `SET_SHIPMENT`, `COLLECT`, `CANCEL`) is set in `application.yaml` under `events.listen`. The queue bindings are built from that list. | The Java code never contains the word "order"; a different shop only changes the config | Accepted |
| M43 | A courier receipt is all or nothing: every tracking number must exist, belong to that courier and be `COLLECTED`; otherwise nothing is saved and every problem is listed. The proof file (PDF or photo) is required. The receipt and the `PAID` payments are saved in one transaction. | Money is never accepted for a parcel the system thinks is still on the road; every receipt has its proof | Accepted |
| M35 | Staging maps only the Nginx port. RabbitMQ UI and Mailpit are reached locally through Nginx (`rabbitmq.localhost`, `mail.localhost`). | Smallest attack surface on the server | Accepted |
