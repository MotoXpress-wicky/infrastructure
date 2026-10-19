# API map (MVP)

Every URL in the MVP. **Built** = exists today. Everything else is **Planned**.

Access words: **Public** (no login) · **Login** · **Owner** (logged in, your own order) ·
**Admin** (`ROLE_ADMIN`) · **Internal** (path starts with `/internal/`; only another service
calls it; Nginx never routes it).

## Host names and ports (laptop)

| Host / part | Port | What |
|---|---|---|
| `http://localhost` | 80 | Customer site + API (Nginx) |
| `http://admin.localhost` | 80 | Admin site + API (Nginx) |
| users-ui / admin-ui (Vite) | 3000 / 3001 | Reached through Nginx |
| user / product / order / notification / payment service | 8080 / 8081 / 8082 / 8083 / 8084 | Reached through Nginx |
| PostgreSQL / Redis / RabbitMQ / RabbitMQ UI | 5432 / 6379 / 5672 / 15672 | Helpers |
| Mailpit inbox | TODO: check its port on the Mailpit docs | Helper |

## Nginx routes (same API routes on both hosts)

| Path starts with | Goes to |
|---|---|
| `/api/v1/user/`, `/oauth2/`, `/login/oauth2/` | user-service 8080 |
| `/api/v1/product/` | product-service 8081 |
| `/api/v1/order/` | order-service 8082 |
| `/api/v1/notification/` | notification-service 8083 |
| `/api/v1/payment/` | payment-service 8084 |
| `/` on `localhost` | users-ui 3000 |
| `/` on `admin.localhost` | admin-ui 3001 |

## user-service (8080)

| Method | Path | Access | Does | Status |
|---|---|---|---|---|
| POST | `/api/v1/user/auth/register` | Public + CAPTCHA | Create account | Built |
| POST | `/api/v1/user/auth/login` | Public | Log in, set cookies | Built |
| GET | `/api/v1/user/auth/me` | Login | Who am I | Built |
| POST | `/api/v1/user/auth/refresh` | Refresh cookie | New tokens | Built |
| POST | `/api/v1/user/auth/logout` | Public | Clear cookies | Built |
| POST | `/api/v1/user/auth/forgot-password` | Public + CAPTCHA | Start reset | Built |
| GET | `/api/v1/user/auth/reset-password/validate?token=` | Public | Is the link good? | Built |
| POST | `/api/v1/user/auth/reset-password` | Public | New password | Built |
| GET | `/api/v1/user/profile` | Login | Profile | Built |
| GET | `/oauth2/authorization/google` | Public | Start Google login | Built |
| GET | `/login/oauth2/code/google` | Google | Google comes back | Built |
| GET | `/api/v1/user/admin/users` | Admin | List users | Planned |
| POST | `/api/v1/user/admin/users/{id}/promote` | Admin | Make admin + audit log | Planned |
| POST | `/api/v1/user/admin/users/{id}/lock` | Admin | Lock + audit log | Planned |
| POST | `/api/v1/user/admin/users/{id}/unlock` | Admin | Unlock + audit log | Planned |
| GET | `/api/v1/user/admin/audit-log` | Admin | Audit log | Planned |

## product-service (8081)

| Method | Path | Access | Does |
|---|---|---|---|
| GET | `/api/v1/product/brands` | Public | Active bike brands |
| GET | `/api/v1/product/brands/{brandId}/models` | Public | Models of a brand |
| GET | `/api/v1/product/categories` | Public | Categories |
| GET | `/api/v1/product/products` | Public | Search: `q`, `bikeModelId`, `categoryId`, `page`, `size` |
| GET | `/api/v1/product/products/{id}` | Public | One part, fitment, photo URLs |
| GET | `/api/v1/product/photos/{fileName}` | Public | Photo file |
| POST | `/api/v1/product/admin/brands` | Admin | Add brand |
| PATCH | `/api/v1/product/admin/brands/{id}` | Admin | Rename, hide |
| POST | `/api/v1/product/admin/brands/{brandId}/models` | Admin | Add bike model |
| PATCH | `/api/v1/product/admin/models/{id}` | Admin | Edit, hide |
| POST | `/api/v1/product/admin/categories` | Admin | Add category |
| PATCH | `/api/v1/product/admin/categories/{id}` | Admin | Rename, hide |
| GET | `/api/v1/product/admin/products` | Admin | All parts, hidden too |
| POST | `/api/v1/product/admin/products` | Admin | Add part + fitment + start stock |
| PUT | `/api/v1/product/admin/products/{id}` | Admin | Edit part and fitment |
| PATCH | `/api/v1/product/admin/products/{id}` | Admin | Hide or show |
| POST | `/api/v1/product/admin/products/{id}/photos` | Admin | Upload photo (max 5) |
| DELETE | `/api/v1/product/admin/products/{id}/photos/{photoId}` | Admin | Remove photo |
| POST | `/api/v1/product/admin/products/{id}/stock` | Admin | Add or remove stock with a reason |
| GET | `/api/v1/product/admin/products/{id}/stock` | Admin | Stock history |
| POST | `/internal/v1/product/reservations` | Internal | Reserve stock, return real prices |
| DELETE | `/internal/v1/product/reservations/{orderNo}` | Internal | Release stock |

## order-service (8082)

| Method | Path | Access | Does |
|---|---|---|---|
| POST | `/api/v1/order/orders` | Login | Checkout (cash on delivery) |
| GET | `/api/v1/order/orders` | Login | My orders |
| GET | `/api/v1/order/orders/{orderNo}` | Owner | One order with shipment |
| POST | `/api/v1/order/orders/{orderNo}/cancel` | Owner | Cancel before shipping |
| POST | `/api/v1/order/orders/{orderNo}/received` | Owner | "I received it" |
| GET | `/api/v1/order/admin/orders` | Admin | Orders. Filters: shipment status, payment status, date, overdue |
| GET | `/api/v1/order/admin/orders/summary` | Admin | Counts: to ship, with courier, cash with couriers, overdue |
| GET | `/api/v1/order/admin/orders/{orderNo}` | Admin | One order (also used for the packing slip) |
| POST | `/api/v1/order/admin/orders/{orderNo}/cancel` | Admin | Cancel before shipping |
| GET | `/api/v1/order/admin/shipments` | Admin | Shipments. Filters: courier, status |
| POST | `/api/v1/order/admin/shipments` | Admin | New shipment: order, courier, tracking number, optional photo |
| POST | `/api/v1/order/admin/shipments/delivered` | Admin | Mark one or many delivered |
| POST | `/api/v1/order/admin/shipments/returned` | Admin | Mark one or many returned, with a reason |
| GET | `/api/v1/order/admin/shipments/{id}/pickup-receipt` | Admin | The pickup receipt photo |

## notification-service (8083)

| Method | Path | Access | Does |
|---|---|---|---|
| POST | `/api/v1/notification/push-devices` | Login | Save this browser's Firebase token |
| DELETE | `/api/v1/notification/push-devices/{token}` | Login | Remove it |

## payment-service (8084)

| Method | Path | Access | Does |
|---|---|---|---|
| GET | `/api/v1/payment/admin/payments` | Admin | Payments. Filters: status, courier, reference, tracking number |
| GET | `/api/v1/payment/admin/payments/{paymentNo}` | Admin | One payment |
| GET | `/api/v1/payment/admin/courier-receipts` | Admin | Courier receipts |
| POST | `/api/v1/payment/admin/courier-receipts` | Admin | New receipt: details + PDF + tracking numbers → payments PAID |
| GET | `/api/v1/payment/admin/courier-receipts/{id}` | Admin | One receipt with its payments |
| GET | `/api/v1/payment/admin/courier-receipts/{id}/file` | Admin | Download the PDF |

## Error codes

Every service uses the same 7-field JSON as user-service:
`timestamp, status, code, message, path, refreshable, details`.

| Service | Codes it adds |
|---|---|
| All | `VALIDATION_FAILED`, `UNAUTHENTICATED`, `ACCESS_TOKEN_EXPIRED`, `ACCESS_TOKEN_INVALID`, `ACCESS_DENIED`, `NOT_FOUND`, `INTERNAL_ERROR` |
| user-service | `CANNOT_LOCK_SELF` |
| product-service | `PART_NUMBER_TAKEN`, `NAME_TAKEN`, `CATEGORY_IN_USE`, `BIKE_MODEL_IN_USE`, `STOCK_BELOW_ZERO`, `OUT_OF_STOCK`, `INVALID_FILE`, `TOO_MANY_PHOTOS` |
| order-service | `OUT_OF_STOCK`, `INVALID_ORDER_STATUS`, `TRACKING_NUMBER_TAKEN`, `PRODUCT_SERVICE_UNAVAILABLE`, `INVALID_FILE` |
| payment-service | `RECEIPT_ALREADY_ENTERED`, `TRACKING_NUMBER_UNKNOWN`, `WRONG_COURIER`, `PAYMENT_NOT_COLLECTED`, `INVALID_FILE` |
| notification-service | — (only the common codes) |

`NOT_FOUND` is new: user-service does not have it yet.
