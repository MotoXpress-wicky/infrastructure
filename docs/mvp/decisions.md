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
| 10, 11 | GitOps: CI builds an image, updates the tag in `k8s/`, ArgoCD deploys; Kustomize base + overlays |
| 12 | API paths `/api/v1/<service>/...` |
| 13 | On the laptop, Docker Compose runs only helpers; services and UIs run on the laptop |
| 14 | Practice Kubernetes on a local cluster (kind or minikube) before paying for a cloud cluster |
| 15 | Cloud: Azure, built with Terraform |
| 16 | Email through SMTP; Mailpit on the laptop |
| 36 | Stock is reserved over HTTP when an order is placed, released on cancel |
| 37 | The cart lives in the browser |

**Not in the MVP:** card payments and OnePay (18–24), refunds, recommendations (21, 27–33, 35).
Their design stays in `../architecture/` for later.

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
| M11 | One codebase. These repos are the **development environment**: laptop + dev cloud + CI/CD. Staging and production are added later as new Kustomize overlays and Terraform folders, each with its own databases and secrets. | Build an image once, promote the same image; no copied code that drifts | Accepted |
| M12 | Login is required to buy. Browsing is public. | Orders, cancel and notifications need a known user | Proposed |
| M13 | A part has a unique part number, one category, fits zero or more bike models or is universal, has an optional part brand and a condition (New or Used) | Matches how riders search: by bike or by part number | Proposed |
| M14 | Nothing in the catalog is deleted; it is hidden | Old orders still point to it | Proposed |
| M15 | One flat delivery fee, set in order-service config | Simple; changes without code | Proposed |
| M16 | product-service publishes no events in the MVP | Nobody listens yet | Proposed |
| M17 | JWT signed with RS256. user-service has the private key; other services get the public key through config | Only user-service can create tokens (decision 3) | Proposed |
| M18 | Files (part photos, courier receipt PDFs, pickup receipt photos) go through a `FileStorage` interface: a folder on the laptop, cloud storage in the dev cloud | Same code everywhere; only config changes | Proposed |
| M19 | Publish an event only after the database transaction commits. A reliable "outbox" comes later. | Never announce something that was rolled back | Proposed |
| M20 | All emails and push messages go through notification-service. Templates and the event → template map live in its config. | One place; stays domain-free | Accepted |
| M21 | The customer's "I received it" button is evidence only. It changes no status. | Only the courier receipt proves the money arrived | Proposed |
| M22 | No "confirmation call" status in the MVP | Add it only if fake orders become a problem | Proposed |
| M23 | When the admin marks a parcel returned, its stock reservation is released. The admin corrects stock by hand if the part came back damaged. | The part is back on the shelf | Proposed |
| M24 | `order.paid` is not published in the MVP | Nobody listens to it yet (no recommendations) | Proposed |
| M25 | Dev cloud on Azure: managed Kubernetes, managed PostgreSQL, a container registry, blob storage; RabbitMQ, Redis and Mailpit run inside the cluster | Cheap enough for dev; same shape as production later | Draft |
