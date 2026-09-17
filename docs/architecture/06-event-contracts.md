# motoXpress event contract (v1)

Status: agreed 2026-09-17.

The single source of truth for RabbitMQ events in motoXpress. Every service must
follow this. For the "why" behind it, read `claude/rabbitmq-notes.md`.

---

## Broker setup

| Item | Value |
|---|---|
| Broker | RabbitMQ |
| Exchange | `app.events` |
| Exchange type | `topic` |
| Durable | yes |

Who declares what:

| Object | Declared by |
|---|---|
| exchange | publisher and consumer |
| queue | consumer only |
| binding | consumer only |

---

## Rules

1. An event name is a fact, past tense: `<thing>.<what happened>`, lowercase, dots.
2. Named in the publisher's own words. Never the listener's words.
3. Once bound to, a name is never renamed. Add a new event instead.
4. Every message carries a `messageId` header (a UUID), set by the publisher.

---

## Event catalog

| Event name | Publisher | Published when |
|---|---|---|
| `user.registered` | user-service | a new account is created |
| `user.password.reset` | user-service | a password reset link is requested |
| `user.password.changed` | user-service | the password is changed |
| `order.placed` | order-service | an order is created |
| `order.paid` | order-service | the order is fully paid |
| `order.shipped` | order-service | the order leaves the warehouse |
| `payment.succeeded` | payment-service | the gateway confirms the money |
| `payment.failed` | payment-service | the gateway rejects the payment |
| `product.created` | product-service | a product is added |
| `product.updated` | product-service | a product is edited |
| `product.deleted` | product-service | a product is removed |

---

## Subscriptions

| Consumer | Queue | Binding keys |
|---|---|---|
| order-service | `order.payment-events` | `payment.succeeded`, `payment.failed` |
| notification-service | `notification.email` | `user.registered`, `user.password.reset`, `user.password.changed`, `order.placed`, `order.paid` |
| notification-service | `notification.push` | `order.paid`, `order.shipped` |
| recommendation-service | `reco.interactions` | `order.paid` |
| recommendation-service | `reco.catalog` | `product.*` |

---

## Message body

Small and generic. Ids and the few values consumers need, not whole entities.
Include what every consumer of that event needs.

Example — `order.paid`:

```json
{
  "userId":  "42",
  "email":   "nimal@example.com",
  "name":    "Nimal Perera",
  "orderNo": "MX-10231",
  "total":   "12500.00"
}
```
