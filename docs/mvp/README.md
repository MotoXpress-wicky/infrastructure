# motoXpress MVP — architecture

The design of the **first version** of motoXpress: a website that sells motorbike parts for
Japanese bikes in Sri Lanka. Customers browse, order, and pay **cash on delivery**. A courier
company delivers. Admins run the catalog, stock, shipments, and the cash that couriers pay back.

`../architecture/` holds the bigger, future system (card payments, recommendations).
**This folder is what we build now.**

## Read in this order

| # | File | C4 kind | Answers |
|---|---|---|---|
| 1 | [01-business-requirements.md](01-business-requirements.md) | — | What must the shop do? How does cash on delivery work? Rules? |
| 2 | [02-domain-model.md](02-domain-model.md) | — | Which business words exist, and which service owns each? |
| 3 | [03-context-diagram.md](03-context-diagram.md) | Level 1 | Who uses it, which outside systems does it call? |
| 4 | [04-container-diagram.md](04-container-diagram.md) | Level 2 | Which parts run on their own, and how do they talk? |
| 5 | [05-components/](05-components/) | Level 3 | What is inside each service and UI? |
| 6 | [06-dynamic/](06-dynamic/) | Dynamic | Step by step: what happens in each scenario? |
| 7 | [07-events.md](07-events.md) | — | Which events exist, with which fields? |
| 8 | [08-data-model.md](08-data-model.md) | — | Which tables does each database have? |
| 9 | [09-state-diagrams.md](09-state-diagrams.md) | — | Which statuses can an order, payment, shipment have? |
| 10 | [10-api-map.md](10-api-map.md) | — | Every URL, owner, access rule, error code |
| 11 | [11-local-deployment.md](11-local-deployment.md) | Deployment | Local environment: the whole system on your PC, and how to debug one service in IntelliJ |
| 12 | [12-dev-cloud.md](12-dev-cloud.md) | Deployment | All environments: local now, staging (VPS) later |
| 13 | [13-ci-cd.md](13-ci-cd.md) | — | How does code get from a pull request to an image and a tag? |
| — | [decisions.md](decisions.md) | — | Why we chose each design |

Components: [user-service](05-components/user-service.md) · [product-service](05-components/product-service.md) ·
[order-service](05-components/order-service.md) · [payment-service](05-components/payment-service.md) ·
[notification-service](05-components/notification-service.md) · [users-ui](05-components/users-ui.md) ·
[admin-ui](05-components/admin-ui.md)

Flows: [auth](06-dynamic/auth.md) · [browse](06-dynamic/browse.md) · [checkout](06-dynamic/checkout.md) ·
[shipping and cash](06-dynamic/after-order.md) · [notifications](06-dynamic/notifications.md) ·
[admin catalog](06-dynamic/admin-catalog.md) · [admin users](06-dynamic/admin-users.md)

## The MVP in one table

| Item | Choice |
|---|---|
| Services | user (built), product, order, payment, notification |
| UIs | users-ui at `localhost`, admin-ui at `admin.localhost` |
| Payment | Cash on delivery only |
| Delivery | Courier companies; the admin enters tracking numbers and courier receipts by hand |
| Order columns | `shipment_status` (NOT_SHIPPED, IN_TRANSIT, DELIVERED, RETURNED, CANCELLED) and `payment_status` (PENDING, COLLECTED, PAID, CANCELLED) |
| Notifications | Email + push (Firebase) |
| Running it | Docker Compose everywhere; images in GitHub Container Registry, built by CI from `main` |
| Environments | `infrastructure/environments/local` (your PC) and `environments/staging` (a VPS, later). Each has a complete `docker-compose.yml`; pipelines write the image tags. |

## How to read every diagram

| Shape | Meaning |
|---|---|
| Rounded `([ ])` | A person, or another service seen from outside |
| Box `[ ]` | Our own service, or a part inside it |
| Cylinder `[( )]` | A database or file store |
| Hexagon `{{ }}` | RabbitMQ |
| Slanted `[/ /]` | A RabbitMQ queue |
| Double box `[[ ]]` | An outside system |
| Solid arrow | HTTP. The caller waits. |
| Dotted arrow | An event. The sender does not wait. |
| **Dashed border** | **Planned** (not built yet) |

In sequence diagrams the numbers are the step order. `->>` call, `-->>` answer, `--)` event.

## Build order (suggested)

Each step ends with something you can click and test.

| Step | Build | Test it by |
|---|---|---|
| 1 | Update `infrastructure/local` and start the helpers | `docker compose ps` all healthy |
| 2 | user-service: Flyway, RS256 keys, bootstrap admin, `user.*` events. Add CI. | Log in at `localhost`; see the event in the RabbitMQ UI |
| 3 | notification-service: email | Forgot password → the email shows in Mailpit |
| 4 | product-service + admin-ui Parts, Catalog, Stock pages | Add Honda → XR 250 → a sprocket with a photo |
| 5 | users-ui browse and cart | Pick XR 250, see the sprocket, add it to the cart |
| 6 | order-service checkout + My orders + admin Orders page | Place an order; stock goes down; "order received" email |
| 7 | payment-service + admin Payments page | A Pending payment appears for the order |
| 8 | Shipments + Courier receipts pages | Ship, deliver, enter a receipt → order shows Delivered + Paid |
| 9 | Push notifications (Firebase) | Phone shows "your order is on its way" |
| 10 | A `Dockerfile`, `ci.yml` and `cd.yml` in every service repo (13-ci-cd.md) | After a merge: `git pull` + `docker compose pull && docker compose up -d` runs the new image |

## Status (2026-10-29)

| Part | State |
|---|---|
| product-service, order-service, notification-service, payment-service | Built, with tests. Verified on PostgreSQL 17 (not yet with RabbitMQ and Docker together) |
| user-service | Flyway (V1, V2), `user.*` events, trace id, new paths, first admin at start-up, admin endpoints and audit log: built. Old `EmailService` removed. Not built: RS256 keys |
| users-ui | Browse, cart, checkout, my orders: built. Not built: push notifications |
| admin-ui | Orders, Shipments, Payments, Courier receipts, Parts (with photos and stock), Catalog, Users (with audit log): all built |
| Dockerfile + `ci.yml` | Written for all seven repos. Images not built yet (Docker was off). `cd.yml` is not written (registry choice open) |

## Open questions

| Where | Question |
|---|---|
| [auth](06-dynamic/auth.md) | Google login behind Nginx: does Spring use the forwarded headers? |
| [events](07-events.md) | An "outbox" table so no event is lost when RabbitMQ is down at the moment of publishing (M19) |
| [12-dev-cloud.md](12-dev-cloud.md) | For staging later: domain name, VPS provider and size, off-site backup tool |
| [13-ci-cd.md](13-ci-cd.md) | Which token type CD uses to commit to the infrastructure repo |
| Courier | Ask your courier: payout frequency, receipt format (PDF or Excel), fees, portal or API |
