# API map

One list of every URL in motoXpress: who owns it, who may call it, and if it is built.

- **Built** = the code exists today (only user-service).
- **Planned** = a proposal. The names may still change when you build the service.
- **Login** = the caller must send a valid `access_token` cookie.
- **Admin** = the token must have `ROLE_ADMIN`.

Every error, from every service, uses the same JSON shape
(see "Rules every service follows" in [02-container-diagram.md](02-container-diagram.md)).

## Public and internal paths

| Kind | Starts with | Who calls it | Routed by Nginx? |
|---|---|---|---|
| Public | `/api/v1/<service>/` | Browser (users-ui, admin-ui), OnePay webhook | Yes |
| Internal | `/internal/v1/<service>/` | Only another service | **No.** Nginx has no rule for it, so the internet cannot reach it. |

## Ports

| Part | Port |
|---|---|
| Nginx customer site / admin site | 80 / 8000 |
| users-ui / admin-ui | 3000 / 3001 |
| user-service | 8080 |
| product-service | 8081 |
| order-service | 8082 |
| notification-service | 8083 (no HTTP API, health check only) |
| payment-service | 8084 |
| recommendation-service | 8085 |
| PostgreSQL / Redis / RabbitMQ / RabbitMQ UI | 5432 / 6379 / 5672 / 15672 |

---

## user-service (8080)

| Method | Path | Access | What it does | Status |
|---|---|---|---|---|
| POST | `/api/v1/user/auth/register` | Public + CAPTCHA | Create an account | Built |
| POST | `/api/v1/user/auth/login` | Public | Check email and password; set both cookies | Built |
| GET | `/api/v1/user/auth/me` | Login | Who am I (id, name, email, roles) | Built |
| POST | `/api/v1/user/auth/refresh` | Refresh cookie | New access token; the refresh token is rotated | Built |
| POST | `/api/v1/user/auth/logout` | Public | Clear both cookies | Built |
| POST | `/api/v1/user/auth/forgot-password` | Public + CAPTCHA | Start a password reset | Built |
| GET | `/api/v1/user/auth/reset-password/validate?token=` | Public | Is this reset link still good? | Built |
| POST | `/api/v1/user/auth/reset-password` | Public | Set a new password with the reset token | Built |
| GET | `/api/v1/user/profile` | Login | Profile data | Built |
| GET | `/oauth2/authorization/google` | Public | Start Google login (Spring Security owns it) | Built |
| GET | `/login/oauth2/code/google` | Google only | Google sends the user back here | Built |
| GET | `/api/v1/user/admin/users` | Admin | List users | Planned |
| POST | `/api/v1/user/admin/users/{id}/promote` | Admin | Give `ROLE_ADMIN`; writes the audit log (decision 8) | Planned |
| GET | `/api/v1/user/admin/audit-log` | Admin | Who changed which role, and when | Planned |
| GET | `/internal/v1/user/public-key` | Other services | Public key to check tokens (decision 3, Proposed) | Planned |

Rate limits (from `RateLimitFilter` and `application.yaml`): login, register, forgot-password,
reset-password and validate are limited per IP. Login and forgot-password are also limited per email.

## product-service (8081) — Planned

| Method | Path | Access | What it does |
|---|---|---|---|
| GET | `/api/v1/product/products` | Public | List products. Filters: category, vehicle, text search |
| GET | `/api/v1/product/products/{id}` | Public | One product |
| GET | `/api/v1/product/categories` | Public | All categories |
| GET | `/api/v1/product/vehicles` | Public | Makes and models, for the "fits my vehicle" filter |
| POST | `/api/v1/product/products` | Admin | Add a product → event `product.created` |
| PUT | `/api/v1/product/products/{id}` | Admin | Edit a product → event `product.updated` |
| DELETE | `/api/v1/product/products/{id}` | Admin | Remove a product → event `product.deleted` |
| POST | `/internal/v1/product/reservations` | order-service | Reserve stock for one order. Returns the real prices (decision 36) |
| DELETE | `/internal/v1/product/reservations/{orderNo}` | order-service | Release the stock of a cancelled order |

## order-service (8082) — Planned

| Method | Path | Access | What it does |
|---|---|---|---|
| POST | `/api/v1/order/orders` | Login | Checkout. Body: items, address, payment method (`COD` or `CARD`). For `CARD` the answer also has the OnePay page URL |
| GET | `/api/v1/order/orders` | Login | My orders |
| GET | `/api/v1/order/orders/{orderNo}` | Login (owner) | One order and its status |
| POST | `/api/v1/order/orders/{orderNo}/cancel` | Login (owner) | Cancel before shipping |
| GET | `/api/v1/order/admin/orders` | Admin | All orders, filter by status |
| POST | `/api/v1/order/admin/orders/{orderNo}/ship` | Admin | Mark shipped → event `order.shipped` |
| POST | `/api/v1/order/admin/orders/{orderNo}/cash-received` | Admin | Cash on delivery was paid → event `order.paid` |
| POST | `/api/v1/order/admin/orders/{orderNo}/cancel` | Admin | Cancel any order before shipping |

## payment-service (8084) — Planned

| Method | Path | Access | What it does |
|---|---|---|---|
| POST | `/internal/v1/payment/payments` | order-service | Start a payment. Body: reference (the order number), amount, currency, method. For a card it returns the OnePay page URL |
| POST | `/api/v1/payment/webhooks/onepay` | OnePay only | OnePay says how the payment ended. payment-service then **verifies** it with OnePay before it trusts it |

The customer's browser never calls payment-service. After the OnePay page, OnePay sends
the browser back to the users-ui page `/orders/{orderNo}`, which shows the order status.

Open (decision 24): check that OnePay really has a webhook and a "verify transaction" API.
The exact OnePay field names are unknown. Do not guess them.

## recommendation-service (8085) — Planned (Python, FastAPI)

| Method | Path | Access | What it does |
|---|---|---|---|
| GET | `/api/v1/recommendation/me` | Login | Suggested items for the person who is logged in |
| GET | `/api/v1/recommendation/items/{itemId}/similar` | Public | Items like this one (for the product page) |

It uses the generic word "item", not "product", so it stays domain-free.

## notification-service (8083) — Planned

No public or internal API. It only listens to RabbitMQ.

---

## Pages in the UIs

| UI | Page | Status |
|---|---|---|
| users-ui | `/login`, `/register`, `/forgot-password`, `/reset-password`, `/`, `/profile` | Built |
| users-ui | `/products`, `/products/:id`, `/cart`, `/checkout`, `/orders`, `/orders/:orderNo` | Planned |
| admin-ui | `/login`, `/products`, `/orders`, `/users`, `/audit-log` | Planned |
